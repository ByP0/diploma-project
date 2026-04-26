from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import INTEGER, JSONB, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseWithUUId


class OutboxMessage(BaseWithUUId):
    __tablename__ = "outbox_messages"
    __allow_nullable__ = {
        "aggregate_id",
        "headers",
        "exchange_name",
        "routing_key",
        "correlation_id",
        "causation_id",
        "published_at",
        "processed_at",
        "dead_lettered_at",
        "next_retry_at",
        "last_error",
    }
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_outbox_messages_event_id"),
        Index("ix_outbox_messages_status", "status"),
        Index("ix_outbox_messages_destination", "destination"),
        Index("ix_outbox_messages_event_name", "event_name"),
        Index("ix_outbox_messages_next_retry_at", "next_retry_at"),
        Index("ix_outbox_messages_created_at", "created_at"),
    )

    event_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    event_name: Mapped[str] = mapped_column(VARCHAR(128))
    event_kind: Mapped[str] = mapped_column(VARCHAR(32))
    aggregate_type: Mapped[str] = mapped_column(VARCHAR(64))
    aggregate_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    version: Mapped[int]
    correlation_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    causation_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    headers: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(32), default="pending", server_default="pending")
    destination: Mapped[str] = mapped_column(VARCHAR(32), default="local", server_default="local")
    attempts: Mapped[int] = mapped_column(INTEGER, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(INTEGER, default=5, server_default="5")
    exchange_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    routing_key: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
