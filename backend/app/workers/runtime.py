from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable

from app.core.config import setting
from app.db.postgres import db_postgres
from app.events.subscribers.rabbitmq_subscriber import RabbitMQSubscriber
from app.observability.logging import configure_logging


logger = logging.getLogger(__name__)


async def run_periodic_worker(
    *,
    worker_name: str,
    process_once: Callable[[], Awaitable[int]],
    interval_seconds: int | None = None,
) -> None:
    configure_logging()
    interval = interval_seconds or setting.worker_poll_interval_seconds
    logger.info("worker_started", extra={"event": "worker_started", "worker_name": worker_name})
    while True:
        try:
            processed = await process_once()
            logger.info(
                "worker_iteration_completed",
                extra={
                    "event": "worker_iteration_completed",
                    "worker_name": worker_name,
                    "processed": processed,
                },
            )
        except Exception as exc:  # pragma: no cover - runtime guard
            logger.exception(
                "worker_iteration_failed",
                extra={
                    "event": "worker_iteration_failed",
                    "worker_name": worker_name,
                    "reason": str(exc),
                },
            )
        await asyncio.sleep(interval)


async def run_rabbitmq_subscriber_worker(
    *,
    worker_name: str,
    queue_name: str,
    routing_keys: Iterable[str],
) -> None:
    configure_logging()
    logger.info(
        "worker_started",
        extra={
            "event": "worker_started",
            "worker_name": worker_name,
            "queue_name": queue_name,
            "routing_keys": list(routing_keys),
        },
    )
    while True:
        try:
            async with db_postgres.session_factory() as session:
                subscriber = RabbitMQSubscriber(
                    session,
                    consumer_name=worker_name,
                    queue_name=queue_name,
                    routing_key=routing_keys,
                )
                await subscriber.start()
        except Exception as exc:  # pragma: no cover - requires broker runtime
            logger.exception(
                "worker_subscriber_failed",
                extra={
                    "event": "worker_subscriber_failed",
                    "worker_name": worker_name,
                    "reason": str(exc),
                },
            )
            await asyncio.sleep(setting.worker_poll_interval_seconds)
