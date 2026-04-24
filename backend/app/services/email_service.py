from __future__ import annotations

import asyncio
import logging
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import setting
from app.observability.metrics import metrics_registry


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class EmailPayload:
    subject: str
    recipients: list[str]
    text_body: str
    html_body: str | None = None
    template_name: str = "generic"
    reply_to: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EmailDeliveryResult:
    success: bool
    provider: str
    error: str | None = None


class EmailService:
    provider_name = "smtp"

    async def send(self, payload: EmailPayload) -> EmailDeliveryResult:
        if not payload.recipients:
            return EmailDeliveryResult(success=False, provider=self.provider_name, error="No recipients")

        if not setting.smtp_enabled:
            logger.info(
                "email_delivery_skipped",
                extra={
                    "event": "email_delivery_skipped",
                    "template_name": payload.template_name,
                    "recipients": payload.recipients,
                },
            )
            metrics_registry.increment(
                "shop_email_deliveries_total",
                template=payload.template_name,
                status="skipped",
            )
            return EmailDeliveryResult(success=True, provider=f"{self.provider_name}_disabled")

        try:
            await asyncio.to_thread(self._send_sync, payload)
        except Exception as exc:  # pragma: no cover - depends on external smtp
            logger.exception(
                "email_delivery_failed",
                extra={
                    "event": "email_delivery_failed",
                    "template_name": payload.template_name,
                    "recipients": payload.recipients,
                },
            )
            metrics_registry.increment(
                "shop_email_deliveries_total",
                template=payload.template_name,
                status="failed",
            )
            return EmailDeliveryResult(success=False, provider=self.provider_name, error=str(exc))

        metrics_registry.increment(
            "shop_email_deliveries_total",
            template=payload.template_name,
            status="sent",
        )
        return EmailDeliveryResult(success=True, provider=self.provider_name)

    def _send_sync(self, payload: EmailPayload) -> None:
        message = EmailMessage()
        message["Subject"] = payload.subject
        message["From"] = formataddr((setting.smtp_from_name, setting.smtp_from_email))
        message["To"] = ", ".join(payload.recipients)
        if payload.reply_to:
            message["Reply-To"] = ", ".join(payload.reply_to)
        message.set_content(payload.text_body)
        if payload.html_body:
            message.add_alternative(payload.html_body, subtype="html")

        if setting.smtp_use_tls:
            with smtplib.SMTP_SSL(
                host=setting.smtp_host,
                port=setting.smtp_port,
                timeout=setting.smtp_timeout_seconds,
            ) as smtp:
                self._authenticate_if_needed(smtp)
                smtp.send_message(message)
            return

        with smtplib.SMTP(
            host=setting.smtp_host,
            port=setting.smtp_port,
            timeout=setting.smtp_timeout_seconds,
        ) as smtp:
            smtp.ehlo()
            if setting.smtp_use_starttls:
                smtp.starttls()
                smtp.ehlo()
            self._authenticate_if_needed(smtp)
            smtp.send_message(message)

    @staticmethod
    def _authenticate_if_needed(smtp: smtplib.SMTP) -> None:
        if setting.smtp_username and setting.smtp_password:
            smtp.login(setting.smtp_username, setting.smtp_password)
