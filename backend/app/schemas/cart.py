from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.images import build_image_url, build_image_urls


class CartItemCreate(BaseModel):
    product_id: UUID
    quantity: Annotated[int, Field(ge=1)]

    model_config = ConfigDict(extra="forbid")


class CartItemUpdate(BaseModel):
    quantity: Annotated[int, Field(ge=1)]

    model_config = ConfigDict(extra="forbid")


class GuestCartSessionRead(BaseModel):
    guest_cart_id: str
    expires_at: datetime


class CartProductSummary(BaseModel):
    id: UUID
    sku: str
    name: str
    brand: str | None
    price: Decimal
    unit: str
    stock: int
    reserved_stock: int
    photo_ids: list[str]

    @computed_field(return_type=int)
    @property
    def available_stock(self) -> int:
        return max(self.stock - self.reserved_stock, 0)

    @computed_field(return_type=list[str])
    @property
    def photo_urls(self) -> list[str]:
        return build_image_urls(self.photo_ids)

    @computed_field(return_type=str | None)
    @property
    def primary_photo_url(self) -> str | None:
        if not self.photo_ids:
            return None
        return build_image_url(self.photo_ids[0])


class CartItemRead(BaseModel):
    id: UUID
    product_id: UUID
    quantity: int
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    product: CartProductSummary

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    items: list[CartItemRead]
    total_items: int
    total_amount: Decimal
    guest_cart_id: str | None = None
    expires_at: datetime | None = None

    @computed_field(return_type=bool)
    @property
    def is_guest_cart(self) -> bool:
        return self.guest_cart_id is not None

