from __future__ import annotations

from app.events.schemas.envelope import DomainEvent


class PaymentCreated(DomainEvent):
    __aggregate_type__ = "payment"
    __aggregate_id_field__ = "transaction_id"

    transaction_id: str
    order_id: str
    provider_name: str
    operation_type: str
    amount: str
    currency: str


class PaymentAuthorized(DomainEvent):
    __aggregate_type__ = "payment"
    __aggregate_id_field__ = "transaction_id"

    transaction_id: str
    order_id: str
    provider_name: str
    amount: str
    currency: str


class PaymentCaptured(DomainEvent):
    __aggregate_type__ = "payment"
    __aggregate_id_field__ = "transaction_id"

    transaction_id: str
    order_id: str
    provider_name: str
    amount: str
    currency: str


class PaymentFailed(DomainEvent):
    __aggregate_type__ = "payment"
    __aggregate_id_field__ = "transaction_id"

    transaction_id: str
    order_id: str
    provider_name: str
    reason: str | None = None


class PaymentRefunded(DomainEvent):
    __aggregate_type__ = "payment"
    __aggregate_id_field__ = "transaction_id"

    transaction_id: str
    order_id: str
    provider_name: str
    amount: str
    currency: str


class WebhookPaymentReceived(DomainEvent):
    __aggregate_type__ = "payment"
    __aggregate_id_field__ = "transaction_id"

    transaction_id: str
    order_id: str
    provider_name: str
    payment_status: str
