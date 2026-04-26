from __future__ import annotations

import json

from app.core.config import setting
from app.events.schemas.envelope import EventEnvelope

try:  # pragma: no cover - optional dependency at runtime
    import aio_pika
except Exception:  # pragma: no cover - optional dependency at runtime
    aio_pika = None


class RabbitMQPublisher:
    async def publish(
        self,
        envelope: EventEnvelope,
        *,
        exchange_name: str,
        routing_key: str,
    ) -> None:
        if aio_pika is None:
            raise RuntimeError("aio-pika is not installed. RabbitMQ publisher is unavailable.")

        connection = await aio_pika.connect_robust(setting.events_rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=setting.events_rabbitmq_prefetch_count)

            exchange = await channel.declare_exchange(
                exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(
                setting.events_rabbitmq_queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": exchange_name,
                    "x-dead-letter-routing-key": setting.events_rabbitmq_dead_letter_routing_key,
                },
            )
            await queue.bind(exchange, routing_key=setting.events_rabbitmq_queue_routing_key)

            dead_letter_queue = await channel.declare_queue(
                setting.events_rabbitmq_dead_letter_queue_name,
                durable=True,
            )
            await dead_letter_queue.bind(exchange, routing_key=setting.events_rabbitmq_dead_letter_routing_key)

            message = aio_pika.Message(
                body=json.dumps(envelope.model_dump(mode="json")).encode("utf-8"),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=str(envelope.event_id),
                type=envelope.event_name,
            )
            await exchange.publish(message, routing_key=routing_key)
