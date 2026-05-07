from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class OrderStatusHistory(BaseWithUUId):
    __tablename__ = "order_status_history"
    __is_updatable__ = False
    __allow_nullable__ = {"from_status", "actor_user_id", "actor_role", "reason", "details"}
    __table_args__ = (
        Index("ix_order_status_history_order_id", "order_id"),
        Index("ix_order_status_history_to_status", "to_status"),
    )

    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
    )
    from_status: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    to_status: Mapped[str] = mapped_column(VARCHAR(32))
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_role: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    reason: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    order = relationship("Order", lazy="joined", back_populates="status_history")
