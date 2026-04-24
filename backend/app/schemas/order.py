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
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentTransactionRead(BaseModel):
    id: UUID
    provider_name: str
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


class OrderCheckoutCreate(BaseModel):
    customer_name: Annotated[
        str,
        Field(min_length=2, max_length=255),
    ]
    customer_phone: Annotated[
        str,
        Field(min_length=7, max_length=32, pattern=r"^[0-9+()\-\s]+$"),
    ]
    customer_comment: Annotated[
        str | None,
        Field(max_length=1000),
    ] = None
    delivery_method: DeliveryMethodEnum = DeliveryMethodEnum.COURIER
    payment_method: PaymentMethodEnum = PaymentMethodEnum.CARD_ONLINE
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
    def normalize_optional_strings(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator("delivery_country", "currency", mode="after")
    @classmethod
    def upper_short_codes(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return value.upper()

    @model_validator(mode="after")
    def validate_checkout(self) -> "OrderCheckoutCreate":
        if self.delivery_method != DeliveryMethodEnum.PICKUP:
            required_fields = {
                "delivery_address_line1": self.delivery_address_line1,
                "delivery_city": self.delivery_city,
            }
            missing = [field_name for field_name, value in required_fields.items() if not value]
            if missing:
                raise ValueError(
                    "Для доставки необходимо заполнить адрес: delivery_address_line1 и delivery_city."
                )

        if (self.delivery_window_start is None) != (self.delivery_window_end is None):
            raise ValueError("Окно доставки нужно передавать целиком: и начало, и конец.")

        if self.delivery_window_start and self.delivery_window_end:
            if self.delivery_window_end <= self.delivery_window_start:
                raise ValueError("Конец окна доставки должен быть позже начала.")
            if (self.delivery_window_end - self.delivery_window_start).total_seconds() > 24 * 60 * 60:
                raise ValueError("Окно доставки не должно превышать 24 часа.")

        return self

    model_config = ConfigDict(extra="forbid")


class OrderRead(BaseModel):
    id: UUID
    status: OrderStatusEnum
    total_amount: Decimal
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
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]
    payment_transactions: list[PaymentTransactionRead]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: Annotated[OrderStatusEnum, Field()]

    model_config = ConfigDict(extra="forbid")
