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
node frontend/scripts/smoke-localhost.mjs
docker compose down
```

## Services

- API: `http://localhost:4000`
- Web app / Nginx gateway: `http://localhost:8080`
- Web app / direct frontend container: `http://localhost:3000`
- OpenAPI docs: `http://localhost:8080/docs`
- Frontend admin dashboard: `http://localhost:8080/admin`
- Backend SQLAdmin panel: `http://localhost:8080/backend-admin`
- RabbitMQ UI: `http://localhost:15672`

Seed admin user: `admin@example.com` / `admin12345`.
Host ports can be changed in `.env` with `NGINX_PORT`, `FRONTEND_PORT`, `BACKEND_PORT`, `POSTGRES_PORT`, `MONGO_PORT`, `REDIS_PORT`, `RABBITMQ_PORT` and `RABBITMQ_MANAGEMENT_PORT`.
If Docker build fails on `npm ci` or `pip install` while VPN/proxy is enabled, set `HTTP_PROXY`, `HTTPS_PROXY`, `NPM_CONFIG_PROXY`, `NPM_CONFIG_HTTPS_PROXY` and `PIP_PROXY` in `.env`, or reuse a previously built image with `docker compose up -d --no-build`.

## Local Smoke Test

After `docker compose up --build -d` and the services become healthy, run:

```bash
node frontend/scripts/smoke-localhost.mjs
```

The smoke test checks `http://localhost:8080`, the `/integrations/dev` SPA route, backend health through the gateway, and OpenAPI webhook paths. Use `SMOKE_BASE_URL=http://localhost:3000` to check the direct frontend container, or `SMOKE_SKIP_READY=true` while dependent services are still warming up.

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [EVENTS.md](EVENTS.md)
- [API.md](API.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [SECURITY.md](SECURITY.md)
- [RUNBOOK.md](RUNBOOK.md)
- [DATABASE.md](DATABASE.md)
