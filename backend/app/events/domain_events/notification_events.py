from __future__ import annotations

from typing import Any

from pydantic import Field

from app.events.schemas.envelope import DomainEvent


class EmailSendRequested(DomainEvent):
    __aggregate_type__ = "notification"
    __aggregate_id_field__ = "notification_key"

    notification_key: str
    template_name: str
    recipient: str
    subject: str
    body_text: str
    body_html: str | None = None
    context_payload: dict[str, Any] = Field(default_factory=dict)
    max_attempts: int = 3


class SmsSendRequested(DomainEvent):
    __aggregate_type__ = "notification"
    __aggregate_id_field__ = "notification_key"

    notification_key: str
    recipient: str
    body_text: str


class NotificationSent(DomainEvent):
    __aggregate_type__ = "notification"
    __aggregate_id_field__ = "notification_id"

    notification_id: str
    channel: str
    template_name: str
    recipient: str
    provider_name: str


class NotificationFailed(DomainEvent):
    __aggregate_type__ = "notification"
    __aggregate_id_field__ = "notification_id"

    notification_id: str
    channel: str
    template_name: str
    recipient: str
    error: str | None = None
