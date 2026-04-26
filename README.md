# Ecommerce Backend

FastAPI backend for an ecommerce project with auth, catalog, cart, checkout, orders, payments, delivery, notifications, admin panel, event-driven processing, outbox/inbox reliability and worker processes.

## Local Start

1. Copy environment examples:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

2. Start core services:

```bash
docker compose up --build
```

3. Run one-off setup tasks when needed:

```bash
docker compose --profile setup run --rm migrate
docker compose --profile setup run --rm seed
```

4. Start workers:

```bash
docker compose --profile workers up --build
```

## Services

- API: `http://localhost:4000`
- Nginx gateway: `http://localhost`
- OpenAPI docs: `http://localhost/docs`
- Admin panel: `http://localhost/admin`
- RabbitMQ UI: `http://localhost:15672`

Seed admin user: `admin@example.com` / `admin12345`.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [EVENTS.md](EVENTS.md)
- [API.md](API.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [SECURITY.md](SECURITY.md)
- [RUNBOOK.md](RUNBOOK.md)
- [DATABASE.md](DATABASE.md)
