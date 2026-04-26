from __future__ import annotations

from typing import Any

from app.events.schemas.envelope import IntegrationEvent


class AnalyticsSyncRequested(IntegrationEvent):
    __aggregate_type__ = "analytics"
    __aggregate_id_field__ = "event_source_id"

    event_source_id: str
    source_event_name: str
    payload: dict[str, Any]


class CRMUserSyncRequested(IntegrationEvent):
    __aggregate_type__ = "crm"
    __aggregate_id_field__ = "user_id"

    user_id: str
    action: str
    email: str


class CRMOrderSyncRequested(IntegrationEvent):
    __aggregate_type__ = "crm"
    __aggregate_id_field__ = "order_id"

    order_id: str
    action: str
    customer_email: str | None = None
    status: str | None = None


class ERPInventorySyncRequested(IntegrationEvent):
    __aggregate_type__ = "erp"
    __aggregate_id_field__ = "product_id"

    product_id: str
    stock: int
    reserved_stock: int
    reason: str


class ERPOrderSyncRequested(IntegrationEvent):
    __aggregate_type__ = "erp"
    __aggregate_id_field__ = "order_id"

    order_id: str
    status: str
    total_amount: str | None = None


class AdminAlertRequested(IntegrationEvent):
    __aggregate_type__ = "admin_alert"
    __aggregate_id_field__ = "alert_key"

    alert_key: str
    severity: str
    title: str
    message: str
    recipients: list[str]


class ReceiptGenerationRequested(IntegrationEvent):
    __aggregate_type__ = "receipt"
    __aggregate_id_field__ = "order_id"

    order_id: str
    document_type: str


class BackgroundTaskRequested(IntegrationEvent):
    __aggregate_type__ = "background_task"
    __aggregate_id_field__ = "task_key"

    task_key: str
    task_name: str
    payload: dict[str, Any]
