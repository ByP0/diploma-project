from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Request

from app.core.config import setting


@dataclass(frozen=True)
class RateLimitPolicy:
    bucket: str
    requests: int
    window_seconds: int


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._entries: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def resolve_policy(self, request: Request) -> RateLimitPolicy | None:
        if not setting.rate_limit_enabled:
            return None

        path = request.url.path
        if path.startswith("/health") or path.startswith("/metrics"):
            return None
        if path.startswith("/api/auth/"):
            return RateLimitPolicy(
                bucket="auth",
                requests=setting.rate_limit_auth_requests,
                window_seconds=setting.rate_limit_auth_window_seconds,
            )
        if path == "/api/orders/from-cart" or path.endswith("/payments/retry"):
            return RateLimitPolicy(
                bucket="checkout",
                requests=setting.rate_limit_checkout_requests,
                window_seconds=setting.rate_limit_checkout_window_seconds,
            )
        if path.startswith("/api/chat") or path.startswith("/api/support"):
            return RateLimitPolicy(
                bucket="support",
                requests=setting.rate_limit_support_requests,
                window_seconds=setting.rate_limit_support_window_seconds,
            )
        return RateLimitPolicy(
            bucket="default",
            requests=setting.rate_limit_default_requests,
            window_seconds=setting.rate_limit_default_window_seconds,
        )

    def check(self, request: Request) -> tuple[bool, int, RateLimitPolicy | None]:
        policy = self.resolve_policy(request)
        if policy is None:
            return True, 0, None

        now = time.monotonic()
        key = self._build_key(request=request, bucket=policy.bucket)

        with self._lock:
            bucket = self._entries[key]
            while bucket and now - bucket[0] >= policy.window_seconds:
                bucket.popleft()

            if len(bucket) >= policy.requests:
                retry_after = max(1, int(policy.window_seconds - (now - bucket[0])))
                return False, retry_after, policy

            bucket.append(now)
            return True, 0, policy

    def reset(self) -> None:
        with self._lock:
            self._entries.clear()

    def _build_key(self, *, request: Request, bucket: str) -> str:
        client_ip = self._resolve_client_ip(request)
        access_token = request.cookies.get(setting.access_cookie_name)
        token_hash = ""
        if access_token:
            token_hash = hashlib.sha256(access_token.encode("utf-8")).hexdigest()[:12]
        return f"{bucket}:{request.method}:{client_ip}:{token_hash}"

    @staticmethod
    def _resolve_client_ip(request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"


rate_limiter = InMemoryRateLimiter()
