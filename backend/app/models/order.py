import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import NUMERIC, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CONFIRMED = "confirmed"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryMethodEnum(str, enum.Enum):
    COURIER = "courier"
    EXPRESS = "express"
    PICKUP = "pickup"


class PaymentMethodEnum(str, enum.Enum):
    CARD_ONLINE = "card_online"
    CASH_ON_DELIVERY = "cash_on_delivery"
    CARD_ON_DELIVERY = "card_on_delivery"


class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Order(BaseWithUUId):
    __tablename__ = "orders"
    __allow_nullable__ = {
        "customer_email",
        "customer_name",
        "customer_phone",
        "customer_comment",
        "delivery_window_start",
        "delivery_window_end",
        "delivery_address_line1",
        "delivery_address_line2",
        "delivery_city",
        "delivery_region",
        "delivery_postal_code",
        "delivery_floor",
        "delivery_apartment",
        "delivery_entrance",
        "delivery_intercom",
        "delivery_instructions",
    }
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
        CheckConstraint(
            "delivery_window_end IS NULL OR delivery_window_start IS NULL OR delivery_window_end > delivery_window_start",
            name="ck_orders_delivery_window_valid",
        ),
        CheckConstraint("char_length(currency) = 3", name="ck_orders_currency_length"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[OrderStatusEnum] = mapped_column(
        default=OrderStatusEnum.PENDING,
        server_default=OrderStatusEnum.PENDING.name,
    )
    total_amount: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    customer_email: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    customer_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    customer_comment: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    delivery_method: Mapped[DeliveryMethodEnum] = mapped_column(
        default=DeliveryMethodEnum.COURIER,
        server_default=DeliveryMethodEnum.COURIER.name,
    )
    delivery_window_start: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    delivery_window_end: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    delivery_address_line1: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    delivery_address_line2: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    delivery_city: Mapped[str | None] = mapped_column(VARCHAR(128), nullable=True)
    delivery_region: Mapped[str | None] = mapped_column(VARCHAR(128), nullable=True)
    delivery_postal_code: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    delivery_country: Mapped[str] = mapped_column(
        VARCHAR(2),
        default="RU",
        server_default="RU",
    )
    delivery_floor: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    delivery_apartment: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    delivery_entrance: Mapped[str | None] = mapped_column(VARCHAR(32), nullable=True)
    delivery_intercom: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    delivery_instructions: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    payment_method: Mapped[PaymentMethodEnum] = mapped_column(
        default=PaymentMethodEnum.CARD_ONLINE,
        server_default=PaymentMethodEnum.CARD_ONLINE.name,
    )
    payment_status: Mapped[PaymentStatusEnum] = mapped_column(
        default=PaymentStatusEnum.PENDING,
        server_default=PaymentStatusEnum.PENDING.name,
    )
    currency: Mapped[str] = mapped_column(
        VARCHAR(3),
        default="RUB",
        server_default="RUB",
    )

    items = relationship("OrderItem", cascade="all, delete-orphan", lazy="selectin")
    payment_transactions = relationship(
        "PaymentTransaction",
        cascade="all, delete-orphan",
        back_populates="order",
        lazy="selectin",
        order_by="PaymentTransaction.created_at",
    )
