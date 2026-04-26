import enum
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import NUMERIC, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class OrderStatusEnum(str, enum.Enum):
    CREATED = "created"
    AWAITING_PAYMENT = "awaiting_payment"
    PAID = "paid"
    PROCESSING = "processing"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


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
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


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
        "cancellation_reason",
        "invoice_number",
        "receipt_number",
    }
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
        CheckConstraint("items_total_amount >= 0", name="ck_orders_items_total_amount_non_negative"),
        CheckConstraint("delivery_cost >= 0", name="ck_orders_delivery_cost_non_negative"),
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
        default=OrderStatusEnum.CREATED,
        server_default=OrderStatusEnum.CREATED.name,
    )
    items_total_amount: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    delivery_cost: Mapped[Decimal] = mapped_column(NUMERIC(10, 2), default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    price_locked_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
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
    cancellation_reason: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    receipt_number: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)

    items = relationship("OrderItem", cascade="all, delete-orphan", lazy="selectin")
    status_history = relationship(
        "OrderStatusHistory",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="OrderStatusHistory.created_at",
    )
    payment_transactions = relationship(
        "PaymentTransaction",
        cascade="all, delete-orphan",
        back_populates="order",
        lazy="selectin",
        order_by="PaymentTransaction.created_at",
    )
    delivery_shipments = relationship(
        "DeliveryShipment",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DeliveryShipment.created_at",
    )
