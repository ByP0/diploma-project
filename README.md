# Ecommerce Backend

FastAPI backend for an ecommerce project with auth, catalog, cart, checkout, orders, payments, delivery, notifications, admin panel, event-driven processing, outbox/inbox reliability and worker processes.

## Local Start

1. Copy environment examples:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

2. Build and start the local Docker stack:

```bash
docker compose up --build -d
```

3. Seed demo data after the backend becomes healthy:

```bash
docker compose --profile setup run --rm seed
```

4. Optional one-off setup tasks:

```bash
docker compose --profile setup run --rm migrate
```

5. Optional workers:

```bash
docker compose --profile workers up --build -d
```

Useful local commands:

```bash
docker compose ps
docker compose logs -f backend nginx frontend
docker compose down
```

## Services

- API: `http://localhost:4000`
- Web app / Nginx gateway: `http://localhost:8080`
- OpenAPI docs: `http://localhost:8080/docs`
- Frontend admin dashboard: `http://localhost:8080/admin`
- Backend SQLAdmin panel: `http://localhost:8080/backend-admin`
- RabbitMQ UI: `http://localhost:15672`

Seed admin user: `admin@example.com` / `admin12345`.
Host ports can be changed in `.env` with `NGINX_PORT`, `BACKEND_PORT`, `POSTGRES_PORT`, `MONGO_PORT`, `REDIS_PORT`, `RABBITMQ_PORT` and `RABBITMQ_MANAGEMENT_PORT`.
If Docker build fails on `npm ci` or `pip install` while VPN/proxy is enabled, disable the VPN or set `HTTP_PROXY`, `HTTPS_PROXY`, `NPM_CONFIG_PROXY`, `NPM_CONFIG_HTTPS_PROXY` and `PIP_PROXY` in `.env`.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [EVENTS.md](EVENTS.md)
- [API.md](API.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [SECURITY.md](SECURITY.md)
- [RUNBOOK.md](RUNBOOK.md)
- [DATABASE.md](DATABASE.md)
