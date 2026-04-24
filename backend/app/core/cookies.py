from __future__ import annotations

from fastapi import Response

from app.core.config import setting


def _build_cookie_params(*, max_age: int) -> dict[str, object]:
    return {
        "httponly": True,
        "secure": setting.cookie_secure,
        "samesite": setting.cookie_samesite,
        "domain": setting.cookie_domain,
        "path": "/",
        "max_age": max_age,
    }


def set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=setting.access_cookie_name,
        value=token,
        **_build_cookie_params(max_age=setting.access_token_expire_minutes * 60),
    )


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=setting.refresh_cookie_name,
        value=token,
        **_build_cookie_params(max_age=setting.refresh_token_expire_days * 24 * 60 * 60),
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=setting.access_cookie_name,
        path="/",
        domain=setting.cookie_domain,
    )
    response.delete_cookie(
        key=setting.refresh_cookie_name,
        path="/",
        domain=setting.cookie_domain,
    )
