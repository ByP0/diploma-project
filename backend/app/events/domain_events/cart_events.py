from __future__ import annotations

from app.events.schemas.envelope import DomainEvent


class CartCreated(DomainEvent):
    __aggregate_type__ = "cart"
    __aggregate_id_field__ = "cart_id"

    cart_id: str
    owner_type: str
    owner_id: str


class CartItemAdded(DomainEvent):
    __aggregate_type__ = "cart"
    __aggregate_id_field__ = "cart_id"

    cart_id: str
    owner_type: str
    owner_id: str
    product_id: str
    quantity: int


class CartItemRemoved(DomainEvent):
    __aggregate_type__ = "cart"
    __aggregate_id_field__ = "cart_id"

    cart_id: str
    owner_type: str
    owner_id: str
    product_id: str


class CartUpdated(DomainEvent):
    __aggregate_type__ = "cart"
    __aggregate_id_field__ = "cart_id"

    cart_id: str
    owner_type: str
    owner_id: str
    product_id: str
    quantity: int


class CartExpired(DomainEvent):
    __aggregate_type__ = "cart"
    __aggregate_id_field__ = "cart_id"

    cart_id: str
    owner_type: str
    owner_id: str
    expired_items: int
