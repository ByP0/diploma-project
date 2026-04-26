# Security

## Implemented Controls

- JWT access tokens and refresh token rotation.
- Password hashing.
- RBAC permissions for `user`, `admin`, `manager`, `support`.
- User blocking and login audit.
- Admin action audit logs.
- Rate limiting and brute-force protection.
- CSRF validation when auth cookies are present.
- CORS policy.
- Security headers and optional HTTPS redirect/HSTS.
- Pydantic input validation.
- SQLAlchemy parameterized queries.
- Webhook HMAC SHA-256 signature validation.
- Secrets configured through environment variables.

## Production Requirements

- Set `COOKIE_SECURE=true`.
- Set `HTTPS_REDIRECT_ENABLED=true`.
- Set `SECURITY_HSTS_ENABLED=true`.
- Store `JWT_SECRET`, webhook secrets, DB credentials and provider credentials in a secret manager.
- Restrict `/metrics` with `METRICS_TOKEN`.
- Restrict admin panel access at the network layer where possible.
- Rotate refresh tokens and revoke tokens after password reset or user blocking.

## Webhook Signature

Header: `X-Webhook-Signature`

Value format:

```text
sha256=<hex hmac>
```

The signature is calculated over the raw request body.
