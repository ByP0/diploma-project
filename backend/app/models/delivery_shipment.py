from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId
from app.models.order import DeliveryMethodEnum


class DeliveryShipment(BaseWithUUId):
    __tablename__ = "delivery_shipments"
    __allow_nullable__ = {
        "external_delivery_id",
        "tracking_number",
        "request_payload",
        "response_payload",
        "shipped_at",
        "delivered_at",
    }
    __table_args__ = (
        CheckConstraint("quoted_cost >= 0", name="ck_delivery_shipments_quoted_cost_non_negative"),
        Index("ix_delivery_shipments_order_id", "order_id"),
        Index("ix_delivery_shipments_status", "status"),
        Index("ix_delivery_shipments_external_delivery_id", "external_delivery_id"),
        Index("ix_delivery_shipments_tracking_number", "tracking_number"),
    )

    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
    )
    provider_name: Mapped[str] = mapped_column(VARCHAR(64))
    delivery_method: Mapped[DeliveryMethodEnum]
    status: Mapped[str] = mapped_column(VARCHAR(32), default="created", server_default="created")
    quoted_cost: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    external_delivery_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    request_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)

    order = relationship("Order", lazy="joined", back_populates="delivery_shipments")
