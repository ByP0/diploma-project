from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, INTEGER, TIMESTAMP, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseWithUUId


class NotificationMessage(BaseWithUUId):
    __tablename__ = "notification_messages"
    __allow_nullable__ = {
        "body_html",
        "context_payload",
        "provider_name",
        "last_error",
        "next_retry_at",
        "sent_at",
    }
    __table_args__ = (
        CheckConstraint("attempts >= 0", name="ck_notification_messages_attempts_non_negative"),
        CheckConstraint("max_attempts > 0", name="ck_notification_messages_max_attempts_positive"),
        Index("ix_notification_messages_status", "status"),
        Index("ix_notification_messages_next_retry_at", "next_retry_at"),
        Index("ix_notification_messages_template_name", "template_name"),
    )

    channel: Mapped[str] = mapped_column(VARCHAR(32), default="email", server_default="email")
    template_name: Mapped[str] = mapped_column(VARCHAR(64))
    recipient: Mapped[str] = mapped_column(VARCHAR(255))
    subject: Mapped[str] = mapped_column(VARCHAR(255))
    body_text: Mapped[str] = mapped_column(VARCHAR(5000))
    body_html: Mapped[str | None] = mapped_column(VARCHAR(10000), nullable=True)
    context_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(32), default="queued", server_default="queued")
    attempts: Mapped[int] = mapped_column(INTEGER, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(INTEGER, default=3, server_default="3")
    provider_name: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    last_error: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
