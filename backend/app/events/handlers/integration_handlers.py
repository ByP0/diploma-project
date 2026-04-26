from __future__ import annotations

from typing import Any
from uuid import uuid4

from app.core.config import setting
from app.events.domain_events import (
    CartCreated,
    CartExpired,
    CartItemAdded,
    CartItemRemoved,
    CartUpdated,
    InventoryCommitted,
    InventoryReleased,
    InventoryReservationFailed,
    InventoryReserved,
    LowStockDetected,
    NotificationFailed,
    NotificationSent,
    OrderCancelled,
    OrderConfirmed,
    OrderCreated,
    OrderDelivered,
    OrderPacked,
    OrderPaid,
    OrderPaymentFailed,
    OrderProcessingStarted,
    OrderRefunded,
    OrderShipped,
    PaymentAuthorized,
    PaymentCaptured,
    PaymentCreated,
    PaymentFailed,
    PaymentRefunded,
    ShipmentCreated,
    ShipmentDelivered,
    ShipmentFailed,
    ShipmentTrackingUpdated,
    UserBlocked,
    UserEmailVerified,
    UserRegistered,
    WebhookPaymentReceived,
)
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


async def handle_user_registered(event: UserRegistered, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.user_id,
        source_event_name=event.event_name,
        payload={"email": event.email, "role": event.role},
    )
    await context.publisher.publish_integration(
        CRMUserSyncRequested(
            user_id=event.user_id,
            action="registered",
            email=event.email,
        )
    )


async def handle_user_email_verified(event: UserEmailVerified, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.user_id,
        source_event_name=event.event_name,
        payload={"email": event.email},
    )
    await context.publisher.publish_integration(
        CRMUserSyncRequested(
            user_id=event.user_id,
            action="email_verified",
            email=event.email,
        )
    )


async def handle_user_blocked(event: UserBlocked, context: EventContext) -> None:
    await _publish_admin_alert(
        context,
        title="User blocked",
        message=f"User {event.email} was blocked. Reason: {event.blocked_reason or 'not specified'}.",
    )
    await context.publisher.publish_integration(
        CRMUserSyncRequested(
            user_id=event.user_id,
            action="blocked",
            email=event.email,
        )
    )


async def handle_cart_created(event: CartCreated, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.cart_id,
        source_event_name=event.event_name,
        payload={"owner_type": event.owner_type, "owner_id": event.owner_id},
    )


async def handle_cart_item_added(event: CartItemAdded, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.cart_id,
        source_event_name=event.event_name,
        payload={"product_id": event.product_id, "quantity": event.quantity},
    )


async def handle_cart_item_removed(event: CartItemRemoved, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.cart_id,
        source_event_name=event.event_name,
        payload={"product_id": event.product_id},
    )


async def handle_cart_updated(event: CartUpdated, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.cart_id,
        source_event_name=event.event_name,
        payload={"product_id": event.product_id, "quantity": event.quantity},
    )


async def handle_cart_expired(event: CartExpired, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.cart_id,
        source_event_name=event.event_name,
        payload={"expired_items": event.expired_items},
    )
    await _publish_background_task(
        context,
        task_name="cart_expiration_cleanup",
        payload={"cart_id": event.cart_id, "expired_items": event.expired_items},
    )


async def handle_order_created(event: OrderCreated, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.order_id,
        source_event_name=event.event_name,
        payload={"status": "created", "total_amount": event.total_amount, "currency": event.currency},
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="created",
            customer_email=event.customer_email,
            status="created",
        )
    )
    await context.publisher.publish_integration(
        ERPOrderSyncRequested(
            order_id=event.order_id,
            status="created",
            total_amount=event.total_amount,
        )
    )


async def handle_order_confirmed(event: OrderConfirmed, context: EventContext) -> None:
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="confirmed",
            customer_email=event.customer_email,
            status="confirmed",
        )
    )
    await context.publisher.publish_integration(
        ERPOrderSyncRequested(
            order_id=event.order_id,
            status="confirmed",
        )
    )


async def handle_order_paid(event: OrderPaid, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.order_id,
        source_event_name=event.event_name,
        payload={"status": "paid", "total_amount": event.total_amount, "currency": event.currency},
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="paid",
            customer_email=event.customer_email,
            status="paid",
        )
    )
    await context.publisher.publish_integration(
        ERPOrderSyncRequested(
            order_id=event.order_id,
            status="paid",
            total_amount=event.total_amount,
        )
    )
    await context.publisher.publish_integration(
        ReceiptGenerationRequested(
            order_id=event.order_id,
            document_type="receipt",
        )
    )


async def handle_order_payment_failed(event: OrderPaymentFailed, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.order_id,
        source_event_name=event.event_name,
        payload={"status": "payment_failed", "reason": event.reason},
    )
    await _publish_admin_alert(
        context,
        title="Order payment failed",
        message=f"Payment for order {event.order_id} failed. Reason: {event.reason or 'unknown'}.",
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="payment_failed",
            customer_email=event.customer_email,
            status="payment_failed",
        )
    )


async def handle_order_processing_started(event: OrderProcessingStarted, context: EventContext) -> None:
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="processing",
            customer_email=event.customer_email,
            status="processing",
        )
    )
    await context.publisher.publish_integration(
        ERPOrderSyncRequested(
            order_id=event.order_id,
            status="processing",
        )
    )


async def handle_order_packed(event: OrderPacked, context: EventContext) -> None:
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="packed",
            customer_email=event.customer_email,
            status="packed",
        )
    )
    await context.publisher.publish_integration(
        ERPOrderSyncRequested(
            order_id=event.order_id,
            status="packed",
        )
    )


async def handle_order_shipped(event: OrderShipped, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.order_id,
        source_event_name=event.event_name,
        payload={"status": "shipped", "tracking_number": event.tracking_number},
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="shipped",
            customer_email=event.customer_email,
            status="shipped",
        )
    )
    await _publish_background_task(
        context,
        task_name="delivery_status_followup",
        payload={"order_id": event.order_id, "tracking_number": event.tracking_number},
    )


async def handle_order_delivered(event: OrderDelivered, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.order_id,
        source_event_name=event.event_name,
        payload={"status": "delivered"},
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="delivered",
            customer_email=event.customer_email,
            status="delivered",
        )
    )
    await _publish_background_task(
        context,
        task_name="post_delivery_followup",
        payload={"order_id": event.order_id},
    )


async def handle_order_cancelled(event: OrderCancelled, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.order_id,
        source_event_name=event.event_name,
        payload={"status": "cancelled", "reason": event.reason},
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="cancelled",
            customer_email=event.customer_email,
            status="cancelled",
        )
    )
    await context.publisher.publish_integration(
        ERPOrderSyncRequested(
            order_id=event.order_id,
            status="cancelled",
        )
    )


async def handle_order_refunded(event: OrderRefunded, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.order_id,
        source_event_name=event.event_name,
        payload={"status": "refunded", "refunded_amount": event.refunded_amount},
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="refunded",
            customer_email=event.customer_email,
            status="refunded",
        )
    )
    await context.publisher.publish_integration(
        ERPOrderSyncRequested(
            order_id=event.order_id,
            status="refunded",
            total_amount=event.refunded_amount,
        )
    )


async def handle_payment_created(event: PaymentCreated, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.transaction_id,
        source_event_name=event.event_name,
        payload={"provider_name": event.provider_name, "amount": event.amount, "currency": event.currency},
    )


async def handle_payment_authorized(event: PaymentAuthorized, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.transaction_id,
        source_event_name=event.event_name,
        payload={"provider_name": event.provider_name, "amount": event.amount, "currency": event.currency},
    )


async def handle_payment_captured(event: PaymentCaptured, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.transaction_id,
        source_event_name=event.event_name,
        payload={"provider_name": event.provider_name, "amount": event.amount, "currency": event.currency},
    )


async def handle_payment_failed(event: PaymentFailed, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.transaction_id,
        source_event_name=event.event_name,
        payload={"provider_name": event.provider_name, "reason": event.reason},
    )
    await _publish_admin_alert(
        context,
        title="Payment failed",
        message=f"Payment {event.transaction_id} failed for order {event.order_id}.",
    )


async def handle_payment_refunded(event: PaymentRefunded, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.transaction_id,
        source_event_name=event.event_name,
        payload={"provider_name": event.provider_name, "amount": event.amount, "currency": event.currency},
    )


async def handle_webhook_payment_received(event: WebhookPaymentReceived, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.transaction_id,
        source_event_name=event.event_name,
        payload={"provider_name": event.provider_name, "payment_status": event.payment_status},
    )
    await _publish_background_task(
        context,
        task_name="payment_webhook_processing",
        payload={"transaction_id": event.transaction_id, "order_id": event.order_id},
    )


async def handle_inventory_reserved(event: InventoryReserved, context: EventContext) -> None:
    await context.publisher.publish_integration(
        ERPInventorySyncRequested(
            product_id=event.product_id,
            stock=event.stock,
            reserved_stock=event.reserved_stock,
            reason="reserved",
        )
    )


async def handle_inventory_reservation_failed(event: InventoryReservationFailed, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.product_id,
        source_event_name=event.event_name,
        payload={
            "order_id": event.order_id,
            "requested_quantity": event.requested_quantity,
            "available_stock": event.available_stock,
        },
    )
    await _publish_admin_alert(
        context,
        title="Inventory reservation failed",
        message=(
            f"Inventory reservation failed for product {event.product_id} in order {event.order_id}. "
            f"Requested {event.requested_quantity}, available {event.available_stock}."
        ),
    )


async def handle_inventory_committed(event: InventoryCommitted, context: EventContext) -> None:
    await context.publisher.publish_integration(
        ERPInventorySyncRequested(
            product_id=event.product_id,
            stock=event.stock,
            reserved_stock=event.reserved_stock,
            reason="committed",
        )
    )


async def handle_inventory_released(event: InventoryReleased, context: EventContext) -> None:
    await context.publisher.publish_integration(
        ERPInventorySyncRequested(
            product_id=event.product_id,
            stock=event.stock,
            reserved_stock=event.reserved_stock,
            reason="released",
        )
    )


async def handle_low_stock_detected(event: LowStockDetected, context: EventContext) -> None:
    await _publish_admin_alert(
        context,
        title="Low stock detected",
        message=f"Product {event.product_id} reached low stock threshold {event.threshold}.",
    )


async def handle_shipment_created(event: ShipmentCreated, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.shipment_id,
        source_event_name=event.event_name,
        payload={"order_id": event.order_id, "provider_name": event.provider_name},
    )


async def handle_shipment_tracking_updated(event: ShipmentTrackingUpdated, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.shipment_id,
        source_event_name=event.event_name,
        payload={"order_id": event.order_id, "status": event.status, "tracking_number": event.tracking_number},
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="shipment_tracking_updated",
            status=event.status,
        )
    )


async def handle_shipment_delivered(event: ShipmentDelivered, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.shipment_id,
        source_event_name=event.event_name,
        payload={"order_id": event.order_id, "status": "delivered"},
    )
    await context.publisher.publish_integration(
        CRMOrderSyncRequested(
            order_id=event.order_id,
            action="delivered",
            status="delivered",
        )
    )


async def handle_shipment_failed(event: ShipmentFailed, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.shipment_id,
        source_event_name=event.event_name,
        payload={"order_id": event.order_id, "status": event.status},
    )
    await _publish_admin_alert(
        context,
        title="Shipment failed",
        message=f"Shipment {event.shipment_id} failed with status {event.status}.",
    )


async def handle_notification_sent(event: NotificationSent, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.notification_id,
        source_event_name=event.event_name,
        payload={"channel": event.channel, "recipient": event.recipient},
    )


async def handle_notification_failed(event: NotificationFailed, context: EventContext) -> None:
    await _publish_analytics(
        context,
        event_source_id=event.notification_id,
        source_event_name=event.event_name,
        payload={"channel": event.channel, "recipient": event.recipient, "error": event.error},
    )
    await _publish_admin_alert(
        context,
        title="Notification failed",
        message=f"Notification {event.notification_id} failed for {event.recipient}: {event.error or 'unknown error'}.",
    )


async def _publish_analytics(
    context: EventContext,
    *,
    event_source_id: str,
    source_event_name: str,
    payload: dict[str, Any],
) -> None:
    await context.publisher.publish_integration(
        AnalyticsSyncRequested(
            event_source_id=event_source_id,
            source_event_name=source_event_name,
            payload=payload,
        )
    )


async def _publish_admin_alert(
    context: EventContext,
    *,
    title: str,
    message: str,
    severity: str = "warning",
) -> None:
    await context.publisher.publish_integration(
        AdminAlertRequested(
            alert_key=uuid4().hex,
            severity=severity,
            title=title,
            message=message,
            recipients=setting.admin_alert_emails,
        )
    )


async def _publish_background_task(
    context: EventContext,
    *,
    task_name: str,
    payload: dict[str, Any],
) -> None:
    await context.publisher.publish_integration(
        BackgroundTaskRequested(
            task_key=uuid4().hex,
            task_name=task_name,
            payload=payload,
        )
    )
