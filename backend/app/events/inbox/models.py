from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import INTEGER, JSONB, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseWithUUId


class InboxMessage(BaseWithUUId):
    __tablename__ = "inbox_messages"
    __allow_nullable__ = {"processed_at", "last_error", "correlation_id", "dead_lettered_at"}
    __table_args__ = (
        UniqueConstraint("event_id", "consumer_name", name="uq_inbox_messages_event_id_consumer"),
        Index("ix_inbox_messages_status", "status"),
        Index("ix_inbox_messages_source", "source"),
        Index("ix_inbox_messages_consumer_name", "consumer_name"),
        Index("ix_inbox_messages_created_at", "created_at"),
    )

    event_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True))
    event_name: Mapped[str] = mapped_column(VARCHAR(128))
    source: Mapped[str] = mapped_column(VARCHAR(128))
    consumer_name: Mapped[str] = mapped_column(VARCHAR(128))
    correlation_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(VARCHAR(32), default="pending", server_default="pending")
    attempts: Mapped[int] = mapped_column(INTEGER, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(INTEGER, default=5, server_default="5")
    processed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
