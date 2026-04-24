from __future__ import annotations

import logging

from app.core.config import setting
from app.observability.metrics import metrics_registry
from app.services.email_service import EmailPayload, EmailService


logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, email_service: EmailService | None = None) -> None:
        self.email_service = email_service or EmailService()

    async def notify(
        self,
        *,
        kind: str,
        severity: str,
        message: str,
        context: dict[str, object] | None = None,
    ) -> None:
        metrics_registry.increment(
            "shop_alerts_total",
            severity=severity,
            kind=kind,
        )
        log_method = logger.error if severity.lower() in {"error", "critical"} else logger.warning
        log_method(
            "system_alert",
            extra={
                "event": "system_alert",
                "alert_kind": kind,
                "alert_severity": severity,
                "alert_message": message,
                "context": context or {},
            },
        )

        if not setting.admin_alert_emails:
            return

        context_lines = "\n".join(
            f"- {key}: {value}" for key, value in (context or {}).items()
        )
        await self.email_service.send(
            EmailPayload(
                subject=f"[{severity.upper()}] {kind}",
                recipients=setting.admin_alert_emails,
                template_name="system_alert",
                text_body=(
                    f"{message}\n\n"
                    f"{context_lines}" if context_lines else message
                ),
                html_body=(
                    f"<p>{message}</p><pre>{context_lines}</pre>"
                    if context_lines
                    else f"<p>{message}</p>"
                ),
            )
        )
