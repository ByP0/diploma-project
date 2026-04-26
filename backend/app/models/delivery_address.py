from __future__ import annotations

from uuid import UUID

from sqlalchemy import BOOLEAN, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseWithUUId


class DeliveryAddress(BaseWithUUId):
    __tablename__ = "delivery_addresses"
    __allow_nullable__ = {
        "label",
        "line2",
        "region",
        "postal_code",
        "floor",
        "apartment",
        "entrance",
        "intercom",
        "instructions",
    }
    __table_args__ = (
        Index("ix_delivery_addresses_user_id", "user_id"),
        Index("ix_delivery_addresses_is_default", "is_default"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    label: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    recipient_name: Mapped[str] = mapped_column(VARCHAR(255))
    phone: Mapped[str] = mapped_column(VARCHAR(32))
    line1: Mapped[str] = mapped_column(VARCHAR(255))
    line2: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    city: Mapped[str] = mapped_column(VARCHAR(128))
    region: Mapped[str | None] = mapped_column(VARCHAR(128), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    country: Mapped[str] = mapped_column(VARCHAR(2), default="RU", server_default="RU")
    floor: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    apartment: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    entrance: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    intercom: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    instructions: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    is_default: Mapped[bool] = mapped_column(BOOLEAN, default=False, server_default=text("false"))
