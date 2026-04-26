# Deployment

## Local Docker

```bash
docker compose up --build
docker compose --profile workers up --build
docker compose --profile setup run --rm migrate
docker compose --profile setup run --rm seed
```

## Environments

Supported environment names:

- `local`
- `development`
- `staging`
- `production`
- `test`

Required production settings:

- `DATABASE_URL`
- `REDIS_URL`
- `BROKER_URL`
- `JWT_SECRET`
- `SENTRY_DSN`

## Production Topology

- API containers behind Nginx/Ingress.
- Separate workers for outbox, email, payment webhooks, inventory, orders, delivery, analytics and cleanup.
- Managed PostgreSQL.
- Managed Redis.
- Managed RabbitMQ or compatible broker with DLQ.
- Object storage for images.
- CDN in front of images.
- Secret manager for credentials and webhook secrets.
- Centralized logs, metrics, tracing and alerting.

## Kubernetes

Reference manifests live in `deploy/k8s`.

Apply sequence:

```bash
kubectl apply -f deploy/k8s/namespace.yaml
kubectl apply -f deploy/k8s/configmap.yaml
kubectl apply -f deploy/k8s/secret.example.yaml
kubectl apply -f deploy/k8s/job-migrate.yaml
kubectl apply -f deploy/k8s/backend-deployment.yaml
kubectl apply -f deploy/k8s/service-ingress.yaml
kubectl apply -f deploy/k8s/workers.yaml
```

Do not apply `secret.example.yaml` unchanged in production. Replace it with values from the secret manager.
