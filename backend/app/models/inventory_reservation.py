from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, INTEGER, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class InventoryReservation(BaseWithUUId):
    __tablename__ = "inventory_reservations"
    __allow_nullable__ = {"details"}
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_inventory_reservations_quantity_positive"),
        Index("ix_inventory_reservations_order_id", "order_id"),
        Index("ix_inventory_reservations_product_id", "product_id"),
        Index("ix_inventory_reservations_status", "status"),
    )

    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
    )
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
    )
    quantity: Mapped[int] = mapped_column(INTEGER)
    status: Mapped[str] = mapped_column(VARCHAR(32), default="active", server_default="active")
    reason: Mapped[str] = mapped_column(VARCHAR(64), default="order", server_default="order")
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    order = relationship("Order", lazy="joined")
    product = relationship("Product", lazy="joined")
