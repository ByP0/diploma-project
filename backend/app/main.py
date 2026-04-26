from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from typing import Annotated

from fastapi import APIRouter, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.cart import router as cart_router
from app.api.categories import router as categories_router
from app.api.chat import router as chat_router
from app.api.checkout import router as checkout_router
from app.api.delivery import router as delivery_router
from app.api.images import router as images_router
from app.api.notifications import router as notifications_router
from app.api.orders import router as orders_router
from app.api.payments import router as payments_router
from app.api.products import router as products_router
from app.api.support import router as support_router
from app.api.users import router as users_router
from app.cache import cache_service
from app.core.config import setting
from app.core.errors import register_exception_handlers
from app.db.mongo import db_mongo
from app.db.postgres import db_postgres
from app.events.event_bus import get_local_event_bus
from app.observability.logging import configure_logging
from app.observability.metrics import metrics_registry
from app.observability.middleware import ObservabilityMiddleware
from app.observability.security_middleware import CSRFMiddleware, SecurityHeadersMiddleware
from app.schemas.common import HealthResponse

try:
    from starlette.middleware.sessions import SessionMiddleware
except Exception as exc:  # pragma: no cover - depends on optional package install
    SessionMiddleware = None
    session_middleware_import_error = exc
else:
    session_middleware_import_error = None

try:
    from starlette.middleware.cors import CORSMiddleware
    from starlette.middleware.gzip import GZipMiddleware
    from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
except Exception as exc:  # pragma: no cover - optional middleware import guard
    CORSMiddleware = None
    GZipMiddleware = None
    HTTPSRedirectMiddleware = None
    extra_middleware_import_error = exc
else:
    extra_middleware_import_error = None

try:
    from app.admin import setup_admin
except Exception as exc:  # pragma: no cover - depends on optional package install
    setup_admin = None
    admin_import_error = exc
else:
    admin_import_error = None

try:
    import sentry_sdk
except Exception:  # pragma: no cover - optional dependency
    sentry_sdk = None


configure_logging()
logger = logging.getLogger(__name__)

if setting.sentry_dsn and sentry_sdk:
    sentry_sdk.init(
        dsn=setting.sentry_dsn,
        environment=setting.environment,
        traces_sample_rate=0.05,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if setting.events_enabled:
        app.state.event_bus = get_local_event_bus()
        logger.info(
            "event_bus_initialized",
            extra={
                "event": "event_bus_initialized",
                "broker_backend": setting.events_broker_backend,
                "dispatch_immediately": setting.events_dispatch_immediately,
            },
        )
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
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)

if setting.gzip_enabled and GZipMiddleware:
    app.add_middleware(GZipMiddleware, minimum_size=setting.gzip_minimum_size_bytes)

if setting.https_redirect_enabled and HTTPSRedirectMiddleware:
    app.add_middleware(HTTPSRedirectMiddleware)

if setting.cors_allowed_origins and CORSMiddleware:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=setting.cors_allowed_origins,
        allow_credentials=setting.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*", setting.csrf_header_name, setting.webhook_signature_header_name, "X-Correlation-ID"],
        expose_headers=["X-Request-ID", "X-Correlation-ID"],
    )

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

if extra_middleware_import_error:
    logger.warning(
        "optional_middleware_unavailable",
        extra={
            "event": "optional_middleware_unavailable",
            "reason": str(extra_middleware_import_error),
        },
    )

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(products_router)
api_router.include_router(images_router)
api_router.include_router(cart_router)
api_router.include_router(checkout_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
api_router.include_router(delivery_router)
api_router.include_router(notifications_router)
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
    tags=["РЎРµСЂРІРёСЃ"],
    summary="РџСЂРѕРІРµСЂРёС‚СЊ СЃРѕСЃС‚РѕСЏРЅРёРµ СЃРµСЂРІРёСЃР°",
)
async def health():
    return HealthResponse(status="ok", detail="РЎРµСЂРІРёСЃ СЂР°Р±РѕС‚Р°РµС‚ СЃС‚Р°Р±РёР»СЊРЅРѕ.")


@app.get("/health/live", include_in_schema=False)
async def health_live():
    return {"status": "ok", "detail": "Application process is alive."}


@app.get("/health/ready", include_in_schema=False)
async def health_ready():
    checks: dict[str, str] = {}
    is_ready = True

    try:
        async with db_postgres.session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:  # pragma: no cover - runtime readiness path
        checks["postgres"] = f"error:{type(exc).__name__}"
        is_ready = False

    try:
        await db_mongo.database.command("ping")
        checks["mongo"] = "ok"
    except Exception as exc:  # pragma: no cover - runtime readiness path
        checks["mongo"] = f"error:{type(exc).__name__}"
        is_ready = False

    try:
        await cache_service.ping()
        checks["cache"] = f"ok:{cache_service.backend_name}"
    except Exception as exc:  # pragma: no cover - runtime readiness path
        checks["cache"] = f"error:{type(exc).__name__}"
        is_ready = False

    status_code = 200 if is_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "not_ready",
            "checks": checks,
        },
    )


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
