from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Интернет-магазин продуктовых товаров"
    app_description: str = (
        "Сервис интернет-магазина продуктовых товаров с корзиной, заказами и "
        "чат-ботом поддержки на базе ИИ."
    )
    app_version: str = "1.0.0"
    postgres_url: str
    postgres_echo: bool = False
    mongodb_url: str = "mongodb://mongo:27017"
    mongodb_db_name: str = "shop_assets"
    image_bucket_name: str = "product_images"
    image_max_upload_size_bytes: int = 5 * 1024 * 1024
    image_cache_max_age_seconds: int = 60 * 60 * 24 * 30
    secret_key: str = "OnlyForDev!"
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
    admin_alert_emails: list[str] = Field(default_factory=list)
    payment_provider: str = "stub"
    payment_stub_auto_approve: bool = True
    payment_stub_failure_keyword: str = "FAIL_PAYMENT"
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
        if value is None:
            return []
        if isinstance(value, str):
            return [
                item.strip().lower()
                for item in value.split(",")
                if item.strip()
            ]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip().lower() for item in value if str(item).strip()]
        raise ValueError("admin_alert_emails must be a list or comma separated string")

    @field_validator("smtp_from_email", "payment_provider", "log_level", mode="before")
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
