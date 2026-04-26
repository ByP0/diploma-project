from __future__ import annotations

import logging
from uuid import UUID

from app.events.event_bus.base import EventContext
from app.events.integration_events import (
    AdminAlertRequested,
    AnalyticsSyncRequested,
    BackgroundTaskRequested,
    CRMOrderSyncRequested,
    CRMUserSyncRequested,
    ERPInventorySyncRequested,
    ERPOrderSyncRequested,
    ReceiptGenerationRequested,
)
from app.observability.metrics import metrics_registry
from app.services.alert_service import AlertService


logger = logging.getLogger(__name__)


async def handle_analytics_sync_requested(event: AnalyticsSyncRequested, _context: EventContext) -> None:
    _record_external_sync(
        target="analytics",
        action=event.source_event_name,
        aggregate_id=event.event_source_id,
        payload=event.payload,
    )


async def handle_crm_user_sync_requested(event: CRMUserSyncRequested, _context: EventContext) -> None:
    _record_external_sync(
        target="crm",
        action=f"user:{event.action}",
        aggregate_id=event.user_id,
        payload={"email": event.email},
    )


async def handle_crm_order_sync_requested(event: CRMOrderSyncRequested, _context: EventContext) -> None:
    _record_external_sync(
        target="crm",
        action=f"order:{event.action}",
        aggregate_id=event.order_id,
        payload={"customer_email": event.customer_email, "status": event.status},
    )


async def handle_erp_inventory_sync_requested(event: ERPInventorySyncRequested, _context: EventContext) -> None:
    _record_external_sync(
        target="erp",
        action=f"inventory:{event.reason}",
        aggregate_id=event.product_id,
        payload={"stock": event.stock, "reserved_stock": event.reserved_stock},
    )


async def handle_erp_order_sync_requested(event: ERPOrderSyncRequested, _context: EventContext) -> None:
    _record_external_sync(
        target="erp",
        action=f"order:{event.status}",
        aggregate_id=event.order_id,
        payload={"total_amount": event.total_amount},
    )


async def handle_admin_alert_requested(event: AdminAlertRequested, _context: EventContext) -> None:
    await AlertService().notify(
        kind=event.title,
        severity=event.severity,
        message=event.message,
        context={"alert_key": event.alert_key, "recipients": event.recipients},
    )


async def handle_receipt_generation_requested(event: ReceiptGenerationRequested, context: EventContext) -> None:
    from app.services.order_service import OrderService

    document = await OrderService(context.session).build_document(
        order_id=UUID(event.order_id),
        document_type=event.document_type,
    )
    _record_external_sync(
        target="documents",
        action=f"generate:{event.document_type}",
        aggregate_id=event.order_id,
        payload={"document_number": getattr(document, "document_number", None)},
    )


async def handle_background_task_requested(event: BackgroundTaskRequested, _context: EventContext) -> None:
    _record_external_sync(
        target="background",
        action=event.task_name,
        aggregate_id=event.task_key,
        payload=event.payload,
    )


def _record_external_sync(
    *,
    target: str,
    action: str,
    aggregate_id: str,
    payload: dict[str, object],
) -> None:
    metrics_registry.increment(
        "shop_external_sync_events_total",
        target=target,
        action=action,
    )
    logger.info(
        "external_sync_processed",
        extra={
            "event": "external_sync_processed",
            "target": target,
            "action": action,
            "aggregate_id": aggregate_id,
            "payload": payload,
        },
    )
