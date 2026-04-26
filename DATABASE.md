# Database

## Main Tables

- `users`
- `refresh_token`
- `user_login_audit_logs`
- `admin_audit_logs`
- `categories`
- `products`
- `product_discounts`
- `product_reviews`
- `cart_items`
- `orders`
- `order_items`
- `order_status_history`
- `payment_transactions`
- `inventory_reservations`
- `delivery_addresses`
- `delivery_shipments`
- `notification_messages`
- `support_tickets`
- `support_messages`
- `outbox_messages`
- `inbox_messages`

## Key Constraints

- Products have non-negative stock and `stock >= reserved_stock`.
- Cart items have exactly one owner: user or guest cart.
- Payment transactions use unique `idempotency_key`.
- Outbox events use unique `event_id`.
- Inbox events use unique `(event_id, consumer_name)`.
- Reviews have rating `1..5` and status `pending|approved|rejected`.
- Discounts validate percent/fixed type, non-negative value and valid date range.

## Indexes

Indexes exist for frequently queried fields:

- user email and login audit timestamps;
- product category, SKU and stock fields;
- order user/status/payment status;
- payment external ID and idempotency key;
- delivery tracking number and external delivery ID;
- notification status/retry time;
- outbox status/destination/retry time;
- inbox status/source/consumer name.

## Migrations

Run:

```bash
cd backend
python -m alembic upgrade head
```

Container entrypoint:

```bash
python scripts/migrate.py
```
