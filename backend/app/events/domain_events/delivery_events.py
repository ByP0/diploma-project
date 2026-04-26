from __future__ import annotations

from app.events.schemas.envelope import DomainEvent


class ShipmentCreated(DomainEvent):
    __aggregate_type__ = "shipment"
    __aggregate_id_field__ = "shipment_id"

    shipment_id: str
    order_id: str
    provider_name: str
    tracking_number: str | None = None


class ShipmentTrackingUpdated(DomainEvent):
    __aggregate_type__ = "shipment"
    __aggregate_id_field__ = "shipment_id"

    shipment_id: str
    order_id: str
    provider_name: str
    tracking_number: str | None = None
    status: str


class ShipmentDelivered(DomainEvent):
    __aggregate_type__ = "shipment"
    __aggregate_id_field__ = "shipment_id"

    shipment_id: str
    order_id: str
    provider_name: str


class ShipmentFailed(DomainEvent):
    __aggregate_type__ = "shipment"
    __aggregate_id_field__ = "shipment_id"

    shipment_id: str
    order_id: str
    provider_name: str
    status: str
