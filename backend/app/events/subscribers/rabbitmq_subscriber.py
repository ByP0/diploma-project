from __future__ import annotations

import json
from typing import Iterable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import setting
from app.events.event_bus.base import EventContext
from app.events.event_bus.local_bus import get_local_event_bus
from app.events.inbox.service import InboxService
from app.events.publishers.event_publisher import EventPublisher
from app.events.schemas.envelope import EventEnvelope, event_from_envelope

try:  # pragma: no cover - optional dependency at runtime
    import aio_pika
except Exception:  # pragma: no cover - optional dependency at runtime
    aio_pika = None


class RabbitMQSubscriber:
    def __init__(
        self,
        session: AsyncSession,
        *,
        consumer_name: str | None = None,
        queue_name: str | None = None,
        routing_key: str | Iterable[str] | None = None,
    ) -> None:
        self.session = session
        self.consumer_name = consumer_name or setting.events_default_consumer_name
        self.queue_name = queue_name or setting.events_rabbitmq_queue_name
        if routing_key is None:
            self.routing_keys = [setting.events_rabbitmq_queue_routing_key]
        elif isinstance(routing_key, str):
            self.routing_keys = [routing_key]
        else:
            self.routing_keys = [item for item in routing_key if item]
        self.inbox_service = InboxService(session)
        self.publisher = EventPublisher(session)
        self.local_bus = get_local_event_bus()

    async def start(self) -> None:  # pragma: no cover - requires broker runtime
        if aio_pika is None:
            raise RuntimeError("aio-pika is not installed. RabbitMQ subscriber is unavailable.")

        connection = await aio_pika.connect_robust(setting.events_rabbitmq_url)
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=setting.events_rabbitmq_prefetch_count)
            exchange = await channel.declare_exchange(
                setting.events_rabbitmq_exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )
            queue = await channel.declare_queue(self.queue_name, durable=True)
            for routing_key in self.routing_keys:
                await queue.bind(exchange, routing_key=routing_key)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process(requeue=True):
                        payload = json.loads(message.body.decode("utf-8"))
                        envelope = EventEnvelope.model_validate(payload)
                        inbox_message = await self.inbox_service.acquire(
                            event_id=envelope.event_id,
                            event_name=envelope.event_name,
                            source=message.routing_key or self.queue_name,
                            consumer_name=self.consumer_name,
                            payload=envelope.model_dump(mode="json"),
                            correlation_id=envelope.correlation_id,
                        )
                        if inbox_message is None:
                            continue
                        try:
                            await self.local_bus.publish(
                                event=event_from_envelope(envelope),
                                context=EventContext(session=self.session, publisher=self.publisher),
                            )
                        except Exception as exc:
                            should_retry = await self.inbox_service.mark_failed(inbox_message, str(exc))
                            await self.session.commit()
                            if should_retry:
                                raise
                        else:
                            await self.inbox_service.mark_processed(inbox_message)
                            await self.session.commit()
