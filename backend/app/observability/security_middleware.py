from __future__ import annotations

import secrets

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import setting


_SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
_DOCS_PATHS = {"/docs", "/docs/oauth2-redirect", "/redoc"}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Frame-Options", setting.security_frame_options)
        response.headers.setdefault("X-Content-Type-Options", setting.security_content_type_options)
        response.headers.setdefault("Referrer-Policy", setting.security_referrer_policy)
        response.headers.setdefault("Content-Security-Policy", _content_security_policy_for_path(request.url.path))
        if setting.security_hsts_enabled or setting.cookie_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=63072000; includeSubDomains")
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not setting.csrf_enabled or request.method in _SAFE_METHODS:
            return await call_next(request)

        if _is_safe_path(request.url.path):
            return await call_next(request)

        access_cookie = request.cookies.get(setting.access_cookie_name)
        refresh_cookie = request.cookies.get(setting.refresh_cookie_name)
        if not access_cookie and not refresh_cookie:
            return await call_next(request)

        cookie_token = request.cookies.get(setting.csrf_cookie_name)
        header_token = request.headers.get(setting.csrf_header_name)
        if not cookie_token or not header_token or not secrets.compare_digest(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed."},
            )
        return await call_next(request)


def _is_safe_path(path: str) -> bool:
    for safe_path in setting.csrf_safe_paths:
        if safe_path.endswith("/"):
            if path.startswith(safe_path):
                return True
        elif path == safe_path:
            return True
    return False


def _content_security_policy_for_path(path: str) -> str:
    if path in _DOCS_PATHS:
        return setting.security_docs_content_security_policy
    return setting.security_content_security_policy
