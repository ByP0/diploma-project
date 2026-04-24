from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import Annotated

from fastapi import APIRouter, FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse

from app.api.auth import router as auth_router
from app.api.cart import router as cart_router
from app.api.categories import router as categories_router
from app.api.chat import router as chat_router
from app.api.images import router as images_router
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.api.support import router as support_router
from app.api.users import router as users_router
from app.core.config import setting
from app.core.errors import register_exception_handlers
from app.db.mongo import db_mongo
from app.db.postgres import db_postgres
from app.observability.logging import configure_logging
from app.observability.metrics import metrics_registry
from app.observability.middleware import ObservabilityMiddleware
from app.schemas.common import HealthResponse

try:
    from starlette.middleware.sessions import SessionMiddleware
except Exception as exc:  # pragma: no cover - depends on optional package install
    SessionMiddleware = None
    session_middleware_import_error = exc
else:
    session_middleware_import_error = None

try:
    from app.admin import setup_admin
except Exception as exc:  # pragma: no cover - depends on optional package install
    setup_admin = None
    admin_import_error = exc
else:
    admin_import_error = None


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        await db_postgres.dispose()
        db_mongo.close()


app = FastAPI(
    title=setting.app_name,
    description=setting.app_description,
    version=setting.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

register_exception_handlers(app)
app.add_middleware(ObservabilityMiddleware)

if SessionMiddleware:
    app.add_middleware(
        SessionMiddleware,
        secret_key=setting.admin_session_secret or setting.secret_key,
        session_cookie=setting.admin_session_cookie_name,
        same_site=setting.cookie_samesite,
        https_only=setting.cookie_secure,
        max_age=setting.admin_session_max_age_seconds,
    )
elif session_middleware_import_error:
    logger.warning(
        "admin_session_middleware_unavailable",
        extra={
            "event": "admin_session_middleware_unavailable",
            "reason": str(session_middleware_import_error),
        },
    )

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(images_router)
api_router.include_router(cart_router)
api_router.include_router(orders_router)
api_router.include_router(chat_router)
api_router.include_router(support_router)
api_router.include_router(users_router)

app.include_router(api_router)

if setup_admin and SessionMiddleware:
    app.state.admin = setup_admin(app)
elif admin_import_error:
    logger.warning(
        "admin_panel_unavailable",
        extra={
            "event": "admin_panel_unavailable",
            "reason": str(admin_import_error),
        },
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Сервис"],
    summary="Проверить состояние сервиса",
)
async def health():
    return HealthResponse(status="ok", detail="Сервис работает стабильно.")


@app.get(
    "/metrics",
    include_in_schema=False,
    response_class=PlainTextResponse,
)
async def metrics(
    x_metrics_token: Annotated[str | None, Header(alias="X-Metrics-Token")] = None,
):
    if not setting.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics are disabled.")
    if setting.metrics_token and x_metrics_token != setting.metrics_token:
        raise HTTPException(status_code=403, detail="Metrics token is invalid.")
    return PlainTextResponse(
        metrics_registry.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
