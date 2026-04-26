from __future__ import annotations

from app.events.schemas.envelope import DomainEvent


class OrderCreated(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    total_amount: str
    currency: str
    payment_method: str
    delivery_method: str
    customer_email: str | None = None


class OrderConfirmed(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None


class OrderCancelled(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None
    reason: str | None = None


class OrderPaid(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None
    payment_status: str
    total_amount: str | None = None
    currency: str | None = None


class OrderPaymentFailed(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None
    total_amount: str | None = None
    currency: str | None = None
    reason: str | None = None


class OrderProcessingStarted(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None


class OrderPacked(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None


class OrderShipped(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None
    tracking_number: str | None = None


class OrderDelivered(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None


class OrderRefunded(DomainEvent):
    __aggregate_type__ = "order"
    __aggregate_id_field__ = "order_id"

    order_id: str
    user_id: str
    customer_email: str | None = None
    refunded_amount: str
    currency: str | None = None
    reason: str | None = None
