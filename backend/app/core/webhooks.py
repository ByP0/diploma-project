from __future__ import annotations

import hashlib
import hmac

from fastapi import HTTPException, Request, status

from app.core.config import setting


_UNSIGNED_WEBHOOK_ENVIRONMENTS = {"development", "local", "test"}


def verify_webhook_signature(*, body: bytes, signature: str | None, secret: str | None) -> None:
    if not secret:
        if setting.environment in _UNSIGNED_WEBHOOK_ENVIRONMENTS:
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook secret is not configured.",
        )
    if not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Webhook signature is missing.")

    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    normalized = signature.removeprefix("sha256=").strip()
    if not hmac.compare_digest(expected, normalized):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Webhook signature is invalid.")


async def verify_webhook_request(
    *,
    request: Request,
    signature: str | None,
    secret: str | None,
) -> None:
    verify_webhook_signature(
        body=await request.body(),
        signature=signature,
        secret=secret,
    )
