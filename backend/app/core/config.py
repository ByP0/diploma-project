import json
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


StringList = Annotated[list[str], NoDecode]


def parse_string_list(value: object, *, lowercase: bool = False) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                value = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError("Expected a JSON list or comma separated string") from exc
        else:
            items = [item.strip() for item in stripped.split(",") if item.strip()]
            return [item.lower() for item in items] if lowercase else items
    if isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value if str(item).strip()]
        return [item.lower() for item in items] if lowercase else items
    raise ValueError("Expected a list or comma separated string")


class Settings(BaseSettings):
    app_name: str = "Интернет-магазин продуктовых товаров"
    app_description: str = (
        "Сервис интернет-магазина продуктовых товаров с корзиной, заказами и "
        "чат-ботом поддержки на базе ИИ."
    )
    app_version: str = "1.0.0"
    environment: str = "local"
    postgres_url: str = Field(validation_alias=AliasChoices("POSTGRES_URL", "DATABASE_URL"))
    postgres_echo: bool = False
    mongodb_url: str = "mongodb://mongo:27017"
    mongodb_db_name: str = "shop_assets"
    image_bucket_name: str = "product_images"
    image_max_upload_size_bytes: int = 5 * 1024 * 1024
    image_cache_max_age_seconds: int = 60 * 60 * 24 * 30
    secret_key: str = Field(default="OnlyForDev!", validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"))
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    access_cookie_name: str = "access_token"
    refresh_cookie_name: str = "refresh_token"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_domain: str | None = None
    admin_base_url: str = "/admin"
    admin_title: str = "Store Admin"
    admin_session_cookie_name: str = "admin_session"
    admin_session_secret: str | None = None
    admin_session_max_age_seconds: int = 60 * 60 * 8
    smtp_enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = False
    smtp_use_starttls: bool = True
    smtp_timeout_seconds: int = 10
    smtp_from_email: str = "no-reply@example.com"
    smtp_from_name: str = "Store Notifications"
    admin_alert_emails: StringList = Field(default_factory=list)
    payment_provider: str = "stub"
    payment_stub_auto_approve: bool = True
    payment_stub_failure_keyword: str = "FAIL_PAYMENT"
    events_enabled: bool = True
    events_dispatch_immediately: bool = True
    events_broker_backend: str = "rabbitmq"
    events_outbox_batch_size: int = 100
    events_low_stock_threshold: int = 5
    events_outbox_max_attempts: int = 5
    events_inbox_max_attempts: int = 5
    events_retry_base_delay_seconds: int = 30
    events_default_consumer_name: str = "default-consumer"
    events_rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost/",
        validation_alias=AliasChoices("EVENTS_RABBITMQ_URL", "BROKER_URL"),
    )
    events_rabbitmq_exchange_name: str = "shop.events"
    events_rabbitmq_queue_name: str = "shop.events.main"
    events_rabbitmq_queue_routing_key: str = "shop.#"
    events_rabbitmq_dead_letter_queue_name: str = "shop.events.dlq"
    events_rabbitmq_dead_letter_routing_key: str = "shop.dead"
    events_rabbitmq_prefetch_count: int = 20
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"
    redis_default_ttl_seconds: int = 300
    catalog_cache_ttl_seconds: int = 120
    category_cache_ttl_seconds: int = 300
    image_cdn_base_url: str | None = None
    cors_allowed_origins: StringList = Field(default_factory=list)
    cors_allow_credentials: bool = True
    https_redirect_enabled: bool = False
    gzip_enabled: bool = True
    gzip_minimum_size_bytes: int = 1024
    csrf_enabled: bool = True
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"
    csrf_safe_paths: StringList = Field(default_factory=lambda: [
        "/health",
        "/health/live",
        "/health/ready",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/refresh",
        "/api/payments/webhooks/",
        "/api/delivery/webhooks/",
    ])
    brute_force_protection_enabled: bool = True
    brute_force_max_failures: int = 5
    brute_force_window_seconds: int = 300
    brute_force_lockout_seconds: int = 900
    webhook_signature_header_name: str = "X-Webhook-Signature"
    payment_webhook_secret: str | None = None
    delivery_webhook_secret: str | None = None
    security_hsts_enabled: bool = False
    security_frame_options: str = "DENY"
    security_content_type_options: str = "nosniff"
    security_referrer_policy: str = "same-origin"
    security_content_security_policy: str = (
        "default-src 'self'; img-src 'self' data: https:; object-src 'none'; "
        "base-uri 'self'; frame-ancestors 'none'"
    )
    security_docs_content_security_policy: str = (
        "default-src 'self'; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' data: https://cdn.jsdelivr.net; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    worker_poll_interval_seconds: int = 10
    worker_batch_size: int = 100
    sentry_dsn: str | None = Field(default=None, validation_alias=AliasChoices("SENTRY_DSN", "ERROR_TRACKING_DSN"))
    log_level: str = "INFO"
    log_json: bool = True
    metrics_enabled: bool = True
    metrics_token: str | None = None
    rate_limit_enabled: bool = True
    rate_limit_default_requests: int = 120
    rate_limit_default_window_seconds: int = 60
    rate_limit_auth_requests: int = 20
    rate_limit_auth_window_seconds: int = 60
    rate_limit_checkout_requests: int = 10
    rate_limit_checkout_window_seconds: int = 60
    rate_limit_support_requests: int = 30
    rate_limit_support_window_seconds: int = 60
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    @field_validator("admin_alert_emails", mode="before")
    @classmethod
    def normalize_admin_alert_emails(cls, value: object) -> list[str]:
        return parse_string_list(value, lowercase=True)

    @field_validator("cors_allowed_origins", "csrf_safe_paths", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: object) -> list[str]:
        return parse_string_list(value)

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        normalized = value.strip().lower()
        allowed = {"local", "development", "staging", "production", "test"}
        if normalized not in allowed:
            raise ValueError(f"environment must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator(
        "smtp_from_email",
        "payment_provider",
        "events_broker_backend",
        "events_rabbitmq_exchange_name",
        "events_rabbitmq_queue_name",
        "events_rabbitmq_queue_routing_key",
        "events_rabbitmq_dead_letter_queue_name",
        "events_rabbitmq_dead_letter_routing_key",
        "security_frame_options",
        "security_content_type_options",
        "security_referrer_policy",
        "security_content_security_policy",
        "security_docs_content_security_policy",
        "log_level",
        mode="before",
    )
    @classmethod
    def normalize_string_settings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

setting = Settings()
