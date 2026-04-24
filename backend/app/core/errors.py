from __future__ import annotations

from collections.abc import Iterable
import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.alert_service import AlertService


LOCATION_NAMES = {
    "body": "тело запроса",
    "query": "query-параметр",
    "path": "path-параметр",
    "header": "заголовок",
    "cookie": "cookie",
}


logger = logging.getLogger(__name__)


def _format_location(loc: Iterable[Any]) -> str:
    parts = [str(item) for item in loc]
    if not parts:
        return "запрос"

    first = LOCATION_NAMES.get(parts[0], parts[0])
    remainder = ".".join(parts[1:])
    return f"{first}.{remainder}" if remainder else first


def _translate_validation_message(error: dict[str, Any]) -> str:
    error_type = error.get("type", "")
    ctx = error.get("ctx") or {}

    if error_type == "missing":
        return "Поле обязательно."
    if error_type == "string_too_short":
        return f"Длина строки должна быть не меньше {ctx.get('min_length')} символов."
    if error_type == "string_too_long":
        return f"Длина строки должна быть не больше {ctx.get('max_length')} символов."
    if error_type == "string_pattern_mismatch":
        return "Значение не соответствует ожидаемому формату."
    if error_type == "greater_than_equal":
        return f"Значение должно быть не меньше {ctx.get('ge')}."
    if error_type == "greater_than":
        return f"Значение должно быть больше {ctx.get('gt')}."
    if error_type == "less_than_equal":
        return f"Значение должно быть не больше {ctx.get('le')}."
    if error_type == "less_than":
        return f"Значение должно быть меньше {ctx.get('lt')}."
    if error_type in {"int_parsing", "int_type"}:
        return "Ожидается целое число."
    if error_type in {"float_parsing", "float_type", "decimal_parsing"}:
        return "Ожидается числовое значение."
    if error_type == "bool_parsing":
        return "Ожидается логическое значение true или false."
    if error_type == "uuid_parsing":
        return "Ожидается корректный UUID."
    if error_type == "literal_error":
        return "Передано недопустимое значение."
    if error_type == "enum":
        return "Передано значение вне допустимого списка."
    if error_type == "value_error":
        custom_error = ctx.get("error")
        if custom_error:
            return str(custom_error)
    return "Передано некорректное значение."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            {
                "field": _format_location(error.get("loc", [])),
                "message": _translate_validation_message(error),
                "error_type": error.get("type", "validation_error"),
            }
            for error in exc.errors()
        ]
        logger.warning(
            "request_validation_error",
            extra={
                "event": "request_validation_error",
                "path": request.url.path,
                "method": request.method,
                "errors": errors,
            },
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Ошибка валидации запроса.",
                "errors": errors,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Ошибка обработки запроса."
        logger.warning(
            "http_exception",
            extra={
                "event": "http_exception",
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "detail": detail,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": detail},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            extra={
                "event": "unhandled_exception",
                "path": request.url.path,
                "method": request.method,
            },
        )
        await AlertService().notify(
            kind="unhandled_exception",
            severity="error",
            message="В приложении произошла необработанная ошибка.",
            context={
                "path": request.url.path,
                "method": request.method,
                "exception": type(exc).__name__,
            },
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Внутренняя ошибка сервера."},
        )
