from __future__ import annotations

from contextvars import ContextVar, Token


_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_correlation_id_ctx: ContextVar[str | None] = ContextVar("correlation_id", default=None)
_user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)


def bind_request_context(request_id: str, correlation_id: str | None = None) -> tuple[Token[str | None], Token[str | None], Token[str | None]]:
    request_token = _request_id_ctx.set(request_id)
    correlation_token = _correlation_id_ctx.set(correlation_id or request_id)
    user_token = _user_id_ctx.set(None)
    return request_token, correlation_token, user_token


def reset_request_context(tokens: tuple[Token[str | None], Token[str | None], Token[str | None]]) -> None:
    request_token, correlation_token, user_token = tokens
    _request_id_ctx.reset(request_token)
    _correlation_id_ctx.reset(correlation_token)
    _user_id_ctx.reset(user_token)


def bind_user_context(user_id: str | None) -> None:
    _user_id_ctx.set(user_id)


def get_request_id() -> str | None:
    return _request_id_ctx.get()


def get_correlation_id() -> str | None:
    return _correlation_id_ctx.get()


def get_user_id() -> str | None:
    return _user_id_ctx.get()
