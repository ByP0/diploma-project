from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, NUMERIC, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId
from app.models.order import PaymentMethodEnum, PaymentStatusEnum


class PaymentTransaction(BaseWithUUId):
    __tablename__ = "payment_transactions"
    __allow_nullable__ = {
        "external_payment_id",
        "redirect_url",
        "failure_code",
        "failure_reason",
        "request_payload",
        "response_payload",
        "processed_at",
    }
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_payment_transactions_amount_non_negative"),
        CheckConstraint(
            "char_length(currency) = 3",
            name="ck_payment_transactions_currency_length",
        ),
        Index("ix_payment_transactions_order_id", "order_id"),
        Index("ix_payment_transactions_status", "status"),
        Index("ix_payment_transactions_provider_name", "provider_name"),
        UniqueConstraint(
            "idempotency_key",
            name="uq_payment_transactions_idempotency_key",
        ),
    )

    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
    )
    provider_name: Mapped[str] = mapped_column(VARCHAR(64))
    payment_method: Mapped[PaymentMethodEnum]
    status: Mapped[PaymentStatusEnum]
    amount: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    currency: Mapped[str] = mapped_column(VARCHAR(3))
    idempotency_key: Mapped[str] = mapped_column(VARCHAR(128))
    external_payment_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    redirect_url: Mapped[str | None] = mapped_column(VARCHAR(512), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    request_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    response_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    order = relationship(
        "Order",
        back_populates="payment_transactions",
        lazy="joined",
    )
