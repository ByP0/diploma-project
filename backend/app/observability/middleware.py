from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.observability.context import bind_request_context, reset_request_context
from app.observability.metrics import metrics_registry
from app.observability.rate_limit import rate_limiter


logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = uuid4().hex
        request.state.request_id = request_id
        context_tokens = bind_request_context(request_id)
        started_at = perf_counter()
        response = None

        try:
            allowed, retry_after, policy = rate_limiter.check(request)
            if not allowed:
                path = request.url.path
                metrics_registry.increment(
                    "shop_rate_limit_rejections_total",
                    bucket=policy.bucket if policy else "unknown",
                    path=path,
                )
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Слишком много запросов. Попробуйте немного позже."},
                )
                response.headers["Retry-After"] = str(retry_after)
                response.headers["X-Request-ID"] = request_id
                return response

            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = (perf_counter() - started_at) * 1000
            route = request.scope.get("route")
            normalized_path = getattr(route, "path", request.url.path)
            status_code = response.status_code if response is not None else 500

            metrics_registry.record_http_request(
                method=request.method,
                path=normalized_path,
                status_code=status_code,
                duration_ms=duration_ms,
            )
            logger.info(
                "http_request",
                extra={
                    "event": "http_request",
                    "http_method": request.method,
                    "path": normalized_path,
                    "raw_path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": request.client.host if request.client else "unknown",
                },
            )
            reset_request_context(context_tokens)
