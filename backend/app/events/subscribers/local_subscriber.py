from __future__ import annotations

from app.events.domain_events import (
    CartCreated,
    CartExpired,
    CartItemAdded,
    CartItemRemoved,
    CartUpdated,
    EmailSendRequested,
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
    SmsSendRequested,
    StockChanged,
    UserBlocked,
    UserEmailVerified,
    UserPasswordResetRequested,
    UserRegistered,
    WebhookPaymentReceived,
)
from app.events.event_bus.registry import EventHandlerRegistry, WILDCARD_EVENT
from app.events.handlers import external_sync_handlers, integration_handlers, inventory_handlers, logging_handlers, notification_handlers
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


def build_event_handler_registry() -> EventHandlerRegistry:
    registry = EventHandlerRegistry()

    registry.register(WILDCARD_EVENT, logging_handlers.log_event)

    registry.register(UserRegistered.__name__, notification_handlers.handle_user_registered)
    registry.register(UserPasswordResetRequested.__name__, notification_handlers.handle_user_password_reset_requested)
    registry.register(UserBlocked.__name__, notification_handlers.handle_user_blocked)
    registry.register(OrderCreated.__name__, notification_handlers.handle_order_created)
    registry.register(OrderConfirmed.__name__, notification_handlers.handle_order_confirmed)
    registry.register(OrderPaid.__name__, notification_handlers.handle_order_paid)
    registry.register(OrderPaymentFailed.__name__, notification_handlers.handle_order_payment_failed)
    registry.register(OrderProcessingStarted.__name__, notification_handlers.handle_order_processing_started)
    registry.register(OrderPacked.__name__, notification_handlers.handle_order_packed)
    registry.register(OrderCancelled.__name__, notification_handlers.handle_order_cancelled)
    registry.register(OrderRefunded.__name__, notification_handlers.handle_order_refunded)
    registry.register(OrderShipped.__name__, notification_handlers.handle_order_shipped)
    registry.register(OrderDelivered.__name__, notification_handlers.handle_order_delivered)
    registry.register(EmailSendRequested.__name__, notification_handlers.enqueue_email_request)
    registry.register(SmsSendRequested.__name__, notification_handlers.enqueue_sms_request)

    registry.register(StockChanged.__name__, inventory_handlers.handle_stock_changed)

    registry.register(UserRegistered.__name__, integration_handlers.handle_user_registered)
    registry.register(UserEmailVerified.__name__, integration_handlers.handle_user_email_verified)
    registry.register(UserBlocked.__name__, integration_handlers.handle_user_blocked)
    registry.register(CartCreated.__name__, integration_handlers.handle_cart_created)
    registry.register(CartItemAdded.__name__, integration_handlers.handle_cart_item_added)
    registry.register(CartItemRemoved.__name__, integration_handlers.handle_cart_item_removed)
    registry.register(CartUpdated.__name__, integration_handlers.handle_cart_updated)
    registry.register(CartExpired.__name__, integration_handlers.handle_cart_expired)
    registry.register(OrderCreated.__name__, integration_handlers.handle_order_created)
    registry.register(OrderConfirmed.__name__, integration_handlers.handle_order_confirmed)
    registry.register(OrderPaid.__name__, integration_handlers.handle_order_paid)
    registry.register(OrderPaymentFailed.__name__, integration_handlers.handle_order_payment_failed)
    registry.register(OrderProcessingStarted.__name__, integration_handlers.handle_order_processing_started)
    registry.register(OrderPacked.__name__, integration_handlers.handle_order_packed)
    registry.register(OrderShipped.__name__, integration_handlers.handle_order_shipped)
    registry.register(OrderDelivered.__name__, integration_handlers.handle_order_delivered)
    registry.register(OrderCancelled.__name__, integration_handlers.handle_order_cancelled)
    registry.register(OrderRefunded.__name__, integration_handlers.handle_order_refunded)
    registry.register(PaymentCreated.__name__, integration_handlers.handle_payment_created)
    registry.register(PaymentAuthorized.__name__, integration_handlers.handle_payment_authorized)
    registry.register(PaymentCaptured.__name__, integration_handlers.handle_payment_captured)
    registry.register(PaymentFailed.__name__, integration_handlers.handle_payment_failed)
    registry.register(PaymentRefunded.__name__, integration_handlers.handle_payment_refunded)
    registry.register(WebhookPaymentReceived.__name__, integration_handlers.handle_webhook_payment_received)
    registry.register(InventoryReserved.__name__, integration_handlers.handle_inventory_reserved)
    registry.register(InventoryReservationFailed.__name__, integration_handlers.handle_inventory_reservation_failed)
    registry.register(InventoryCommitted.__name__, integration_handlers.handle_inventory_committed)
    registry.register(InventoryReleased.__name__, integration_handlers.handle_inventory_released)
    registry.register(LowStockDetected.__name__, integration_handlers.handle_low_stock_detected)
    registry.register(ShipmentCreated.__name__, integration_handlers.handle_shipment_created)
    registry.register(ShipmentTrackingUpdated.__name__, integration_handlers.handle_shipment_tracking_updated)
    registry.register(ShipmentDelivered.__name__, integration_handlers.handle_shipment_delivered)
    registry.register(ShipmentFailed.__name__, integration_handlers.handle_shipment_failed)
    registry.register(NotificationSent.__name__, integration_handlers.handle_notification_sent)
    registry.register(NotificationFailed.__name__, integration_handlers.handle_notification_failed)

    registry.register(AnalyticsSyncRequested.__name__, external_sync_handlers.handle_analytics_sync_requested)
    registry.register(CRMUserSyncRequested.__name__, external_sync_handlers.handle_crm_user_sync_requested)
    registry.register(CRMOrderSyncRequested.__name__, external_sync_handlers.handle_crm_order_sync_requested)
    registry.register(ERPInventorySyncRequested.__name__, external_sync_handlers.handle_erp_inventory_sync_requested)
    registry.register(ERPOrderSyncRequested.__name__, external_sync_handlers.handle_erp_order_sync_requested)
    registry.register(AdminAlertRequested.__name__, external_sync_handlers.handle_admin_alert_requested)
    registry.register(ReceiptGenerationRequested.__name__, external_sync_handlers.handle_receipt_generation_requested)
    registry.register(BackgroundTaskRequested.__name__, external_sync_handlers.handle_background_task_requested)

    return registry
