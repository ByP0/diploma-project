from __future__ import annotations

from app.events.schemas.envelope import DomainEvent


class InventoryReserved(DomainEvent):
    __aggregate_type__ = "inventory"
    __aggregate_id_field__ = "product_id"

    product_id: str
    order_id: str
    quantity: int
    stock: int
    reserved_stock: int


class InventoryReservationFailed(DomainEvent):
    __aggregate_type__ = "inventory"
    __aggregate_id_field__ = "product_id"

    product_id: str
    order_id: str
    requested_quantity: int
    available_stock: int


class InventoryReleased(DomainEvent):
    __aggregate_type__ = "inventory"
    __aggregate_id_field__ = "product_id"

    product_id: str
    order_id: str
    quantity: int
    stock: int
    reserved_stock: int


class InventoryCommitted(DomainEvent):
    __aggregate_type__ = "inventory"
    __aggregate_id_field__ = "product_id"

    product_id: str
    order_id: str
    quantity: int
    stock: int
    reserved_stock: int


class StockChanged(DomainEvent):
    __aggregate_type__ = "inventory"
    __aggregate_id_field__ = "product_id"

    product_id: str
    stock: int
    reserved_stock: int
    available_stock: int
    reason: str


class LowStockDetected(DomainEvent):
    __aggregate_type__ = "inventory"
    __aggregate_id_field__ = "product_id"

    product_id: str
    stock: int
    reserved_stock: int
    available_stock: int
    threshold: int
