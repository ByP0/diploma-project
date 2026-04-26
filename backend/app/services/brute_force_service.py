from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request

from app.core.config import setting
from app.observability.metrics import metrics_registry


class BruteForceService:
    def __init__(self) -> None:
        self._entries: dict[str, deque[float]] = defaultdict(deque)
        self._blocked_until: dict[str, float] = {}
        self._lock = Lock()

    def ensure_allowed(self, *, email: str, request: Request | None = None) -> None:
        if not setting.brute_force_protection_enabled:
            return
        now = time.monotonic()
        for key in self._build_keys(email=email, request=request):
            blocked_until = self._blocked_until.get(key)
            if blocked_until and blocked_until > now:
                raise ValueError("Too many failed login attempts. Try again later.")

    def record_failure(self, *, email: str, request: Request | None = None) -> None:
        if not setting.brute_force_protection_enabled:
            return
        now = time.monotonic()
        with self._lock:
            for key in self._build_keys(email=email, request=request):
                bucket = self._entries[key]
                while bucket and now - bucket[0] >= setting.brute_force_window_seconds:
                    bucket.popleft()
                bucket.append(now)
                if len(bucket) >= setting.brute_force_max_failures:
                    self._blocked_until[key] = now + setting.brute_force_lockout_seconds
                    metrics_registry.increment("shop_bruteforce_blocks_total", scope=key.split(":", 1)[0])

    def record_success(self, *, email: str, request: Request | None = None) -> None:
        with self._lock:
            for key in self._build_keys(email=email, request=request):
                self._entries.pop(key, None)
                self._blocked_until.pop(key, None)

    @staticmethod
    def _build_keys(*, email: str, request: Request | None) -> list[str]:
        normalized_email = email.strip().lower()
        client_ip = "unknown"
        if request is not None:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
            elif request.client:
                client_ip = request.client.host
        return [f"email:{normalized_email}", f"ip:{client_ip}"]


brute_force_service = BruteForceService()
