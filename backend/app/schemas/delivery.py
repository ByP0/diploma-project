from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.order import DeliveryMethodEnum


class DeliveryQuoteRequest(BaseModel):
    delivery_method: DeliveryMethodEnum
    city: Annotated[str | None, Field(max_length=128)] = None
    region: Annotated[str | None, Field(max_length=128)] = None
    country: Annotated[str, Field(min_length=2, max_length=2)] = "RU"
    order_amount: Decimal

    @field_validator("city", "region", "country", mode="before")
    @classmethod
    def normalize_strings(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    model_config = ConfigDict(extra="forbid")


class DeliveryQuoteRead(BaseModel):
    provider_name: str
    delivery_method: DeliveryMethodEnum
    cost: Decimal
    currency: str
    estimated_days: int
    details: dict[str, str]


class DeliveryAddressBase(BaseModel):
    label: Annotated[str | None, Field(max_length=64)] = None
    recipient_name: Annotated[str, Field(min_length=2, max_length=255)]
    phone: Annotated[str, Field(min_length=7, max_length=32)]
    line1: Annotated[str, Field(min_length=3, max_length=255)]
    line2: Annotated[str | None, Field(max_length=255)] = None
    city: Annotated[str, Field(min_length=2, max_length=128)]
    region: Annotated[str | None, Field(max_length=128)] = None
    postal_code: Annotated[str | None, Field(max_length=32)] = None
    country: Annotated[str, Field(min_length=2, max_length=2)] = "RU"
    floor: Annotated[str | None, Field(max_length=32)] = None
    apartment: Annotated[str | None, Field(max_length=32)] = None
    entrance: Annotated[str | None, Field(max_length=32)] = None
    intercom: Annotated[str | None, Field(max_length=64)] = None
    instructions: Annotated[str | None, Field(max_length=1000)] = None
    is_default: bool = False

    @field_validator(
        "label",
        "recipient_name",
        "phone",
        "line1",
        "line2",
        "city",
        "region",
        "postal_code",
        "country",
        "floor",
        "apartment",
        "entrance",
        "intercom",
        "instructions",
        mode="before",
    )
    @classmethod
    def normalize_strings(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value


class DeliveryAddressCreate(DeliveryAddressBase):
    model_config = ConfigDict(extra="forbid")


class DeliveryAddressUpdate(BaseModel):
    label: Annotated[str | None, Field(max_length=64)] = None
    recipient_name: Annotated[str | None, Field(min_length=2, max_length=255)] = None
    phone: Annotated[str | None, Field(min_length=7, max_length=32)] = None
    line1: Annotated[str | None, Field(min_length=3, max_length=255)] = None
    line2: Annotated[str | None, Field(max_length=255)] = None
    city: Annotated[str | None, Field(min_length=2, max_length=128)] = None
    region: Annotated[str | None, Field(max_length=128)] = None
    postal_code: Annotated[str | None, Field(max_length=32)] = None
    country: Annotated[str | None, Field(min_length=2, max_length=2)] = None
    floor: Annotated[str | None, Field(max_length=32)] = None
    apartment: Annotated[str | None, Field(max_length=32)] = None
    entrance: Annotated[str | None, Field(max_length=32)] = None
    intercom: Annotated[str | None, Field(max_length=64)] = None
    instructions: Annotated[str | None, Field(max_length=1000)] = None
    is_default: bool | None = None

    @field_validator(
        "label",
        "recipient_name",
        "phone",
        "line1",
        "line2",
        "city",
        "region",
        "postal_code",
        "country",
        "floor",
        "apartment",
        "entrance",
        "intercom",
        "instructions",
        mode="before",
    )
    @classmethod
    def normalize_strings(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    model_config = ConfigDict(extra="forbid")


class DeliveryAddressRead(DeliveryAddressBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryWebhookPayload(BaseModel):
    external_delivery_id: str | None = None
    tracking_number: str | None = None
    status: str
    delivered: bool = False

    model_config = ConfigDict(extra="forbid")
