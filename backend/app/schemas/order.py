from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.order import (
    DeliveryMethodEnum,
    OrderStatusEnum,
    PaymentMethodEnum,
    PaymentStatusEnum,
)


class OrderItemRead(BaseModel):
    id: UUID
    product_id: UUID | None
    product_name: str
    unit_price: Decimal
    quantity: int
    returned_quantity: int
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentTransactionRead(BaseModel):
    id: UUID
    parent_transaction_id: UUID | None
    provider_name: str
    operation_type: str
    payment_method: PaymentMethodEnum
    status: PaymentStatusEnum
    amount: Decimal
    currency: str
    external_payment_id: str | None
    redirect_url: str | None
    failure_code: str | None
    failure_reason: str | None
    processed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryShipmentRead(BaseModel):
    id: UUID
    provider_name: str
    delivery_method: DeliveryMethodEnum
    status: str
    quoted_cost: Decimal
    external_delivery_id: str | None
    tracking_number: str | None
    shipped_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderStatusHistoryRead(BaseModel):
    id: UUID
    from_status: str | None
    to_status: str
    actor_user_id: UUID | None
    actor_role: str | None
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderCheckoutCreate(BaseModel):
    customer_name: Annotated[str, Field(min_length=2, max_length=255)]
    customer_phone: Annotated[str, Field(min_length=7, max_length=32, pattern=r"^[0-9+()\-\s]+$")]
    customer_comment: Annotated[str | None, Field(max_length=1000)] = None
    delivery_method: DeliveryMethodEnum = DeliveryMethodEnum.COURIER
    payment_method: PaymentMethodEnum = PaymentMethodEnum.CARD_ONLINE
    payment_provider: Annotated[str | None, Field(max_length=64)] = None
    delivery_window_start: datetime | None = None
    delivery_window_end: datetime | None = None
    delivery_address_line1: Annotated[str | None, Field(max_length=255)] = None
    delivery_address_line2: Annotated[str | None, Field(max_length=255)] = None
    delivery_city: Annotated[str | None, Field(max_length=128)] = None
    delivery_region: Annotated[str | None, Field(max_length=128)] = None
    delivery_postal_code: Annotated[str | None, Field(max_length=32)] = None
    delivery_country: Annotated[str, Field(min_length=2, max_length=2)] = "RU"
    delivery_floor: Annotated[str | None, Field(max_length=32)] = None
    delivery_apartment: Annotated[str | None, Field(max_length=32)] = None
    delivery_entrance: Annotated[str | None, Field(max_length=32)] = None
    delivery_intercom: Annotated[str | None, Field(max_length=64)] = None
    delivery_instructions: Annotated[str | None, Field(max_length=1000)] = None
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "RUB"

    @field_validator(
        "customer_name",
        "customer_phone",
        "customer_comment",
        "payment_provider",
        "delivery_address_line1",
        "delivery_address_line2",
        "delivery_city",
        "delivery_region",
        "delivery_postal_code",
        "delivery_country",
        "delivery_floor",
        "delivery_apartment",
        "delivery_entrance",
        "delivery_intercom",
        "delivery_instructions",
        "currency",
        mode="before",
    )
    @classmethod
    def normalize_strings(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("delivery_country", "currency", mode="after")
    @classmethod
    def normalize_codes(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.upper()

    @model_validator(mode="after")
    def validate_checkout(self) -> "OrderCheckoutCreate":
        if self.delivery_method != DeliveryMethodEnum.PICKUP:
            if not self.delivery_address_line1 or not self.delivery_city:
                raise ValueError("delivery_address_line1 and delivery_city are required for delivery")

        if (self.delivery_window_start is None) != (self.delivery_window_end is None):
            raise ValueError("delivery window must contain both start and end")

        if self.delivery_window_start and self.delivery_window_end:
            if self.delivery_window_end <= self.delivery_window_start:
                raise ValueError("delivery window end must be after start")
            if (self.delivery_window_end - self.delivery_window_start).total_seconds() > 24 * 60 * 60:
                raise ValueError("delivery window must not exceed 24 hours")

        return self

    model_config = ConfigDict(extra="forbid")


class CheckoutLineRead(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class CheckoutPreviewRead(BaseModel):
    items: list[CheckoutLineRead]
    items_total_amount: Decimal
    delivery_cost: Decimal
    total_amount: Decimal
    currency: str
    delivery_method: DeliveryMethodEnum
    payment_method: PaymentMethodEnum
    calculated_at: datetime


class OrderRead(BaseModel):
    id: UUID
    status: OrderStatusEnum
    items_total_amount: Decimal
    delivery_cost: Decimal
    total_amount: Decimal
    price_locked_at: datetime
    customer_email: str | None
    customer_name: str | None
    customer_phone: str | None
    customer_comment: str | None
    delivery_method: DeliveryMethodEnum
    delivery_window_start: datetime | None
    delivery_window_end: datetime | None
    delivery_address_line1: str | None
    delivery_address_line2: str | None
    delivery_city: str | None
    delivery_region: str | None
    delivery_postal_code: str | None
    delivery_country: str
    delivery_floor: str | None
    delivery_apartment: str | None
    delivery_entrance: str | None
    delivery_intercom: str | None
    delivery_instructions: str | None
    payment_method: PaymentMethodEnum
    payment_status: PaymentStatusEnum
    currency: str
    cancellation_reason: str | None
    invoice_number: str | None
    receipt_number: str | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]
    payment_transactions: list[PaymentTransactionRead]
    status_history: list[OrderStatusHistoryRead] = []
    delivery_shipments: list[DeliveryShipmentRead] = []

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatusEnum
    reason: Annotated[str | None, Field(max_length=1000)] = None

    model_config = ConfigDict(extra="forbid")


class OrderCancelRequest(BaseModel):
    reason: Annotated[str | None, Field(max_length=1000)] = None

    model_config = ConfigDict(extra="forbid")


class OrderRefundItemRequest(BaseModel):
    order_item_id: UUID
    quantity: Annotated[int, Field(ge=1)]

    model_config = ConfigDict(extra="forbid")


class OrderRefundRequest(BaseModel):
    items: list[OrderRefundItemRequest]
    reason: Annotated[str | None, Field(max_length=1000)] = None
    idempotency_key: Annotated[str | None, Field(max_length=128)] = None

    model_config = ConfigDict(extra="forbid")


class OrderDocumentRead(BaseModel):
    document_type: str
    document_number: str
    order_id: UUID
    issued_at: datetime
    amount: Decimal
    currency: str
    items: list[OrderItemRead]
