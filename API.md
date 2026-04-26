# API

OpenAPI is exposed at `/openapi.json`, Swagger UI at `/docs`, ReDoc at `/redoc`.

## Main Areas

- `/api/auth`: registration, login, refresh, logout, password reset and email verification stub.
- `/api/users`: profile, admin user management, login audit.
- `/api/categories`: category CRUD.
- `/api/products`: catalog CRUD, stock fields and cached reads.
- `/api/cart`: user and guest cart operations with 10-day expiry.
- `/api/checkout`: checkout preview, delivery calculation and order confirmation.
- `/api/orders`: user order operations and admin order management.
- `/api/payments`: payment status recheck and provider webhook stubs.
- `/api/delivery`: delivery quotes, addresses and delivery webhooks.
- `/api/notifications`: notification queue operations.
- `/api/support`: support tickets and admin replies.

## Admin Panel

The SQLAdmin panel is mounted at `/admin` and supports:

- products and categories;
- orders and status history;
- users and block flags;
- discounts;
- inventory reservations and stock fields;
- payments;
- delivery shipments;
- notifications;
- login/admin audit logs;
- review moderation;
- support moderation.

## Pagination

List endpoints use `limit` and `offset` where applicable. Heavy endpoints are rate limited.

## Webhooks

Payment and delivery webhooks use HMAC SHA-256 signatures via the `X-Webhook-Signature` header. Payload validation is strict.
