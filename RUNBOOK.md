# Runbook

## Health Checks

- Liveness: `/health/live`
- Readiness: `/health/ready`
- Metrics: `/metrics`

## Outbox Cannot Publish

1. Check RabbitMQ health and credentials.
2. Check `outbox_messages` for `retrying` or `dead_letter`.
3. Inspect `last_error`.
4. Restart `outbox-publisher`.
5. If the broker is healthy, reset safe dead-lettered rows to `pending` after confirming idempotency.

## Consumer Fails During Processing

1. Check `inbox_messages` by `consumer_name`.
2. Rows in `failed` can be retried automatically.
3. Rows in `dead_letter` need manual inspection.
4. Verify handler logs by `correlation_id`.

## Payment Webhook Arrived Twice

Duplicate webhooks are expected. Processing is protected by payment transaction status and idempotent webhook payload checks.

## Product Sold Out During Checkout

Inventory reservation validates available stock. Reservation failure emits `InventoryReservationFailed` and the checkout/order creation fails.

## Paid Order Cancelled

Cancellation triggers refund logic and inventory return. Verify payment transactions, order status history and inventory reservations.

## Reserve Was Not Released

1. Find active rows in `inventory_reservations` for the order.
2. Check order status and payment status.
3. Run release logic through order cancellation or manual admin flow.
4. Emit/verify `InventoryReleased` and `StockChanged`.

## Emergency Contacts

Configure alert recipients with `ADMIN_ALERT_EMAILS`. Production alerting should route metrics/log alerts to the on-call channel.
