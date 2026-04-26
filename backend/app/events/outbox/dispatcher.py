from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import setting
from app.events.outbox.service import OutboxService
from app.events.publishers.rabbitmq_publisher import RabbitMQPublisher
from app.events.schemas.envelope import EventEnvelope


class OutboxDispatcher:
    def __init__(self, session: AsyncSession, publisher: RabbitMQPublisher | None = None) -> None:
        self.session = session
        self.outbox_service = OutboxService(session)
        self.publisher = publisher or RabbitMQPublisher()

    async def dispatch_pending(self, *, limit: int | None = None) -> int:
        pending = await self.outbox_service.list_pending(
            destination="broker",
            limit=limit or setting.events_outbox_batch_size,
        )
        for message in pending:
            envelope = EventEnvelope.model_validate(
                {
                    "event_id": message.event_id,
                    "event_name": message.event_name,
                    "event_kind": message.event_kind,
                    "version": message.version,
                    "correlation_id": message.correlation_id,
                    "causation_id": message.causation_id,
                    "aggregate_type": message.aggregate_type,
                    "aggregate_id": message.aggregate_id,
                    "occurred_at": message.payload.get("occurred_at"),
                    "payload": message.payload,
                    "metadata": message.headers or {},
                }
            )
            try:
                await self.outbox_service.mark_processing(message)
                await self.publisher.publish(
                    envelope,
                    exchange_name=message.exchange_name or setting.events_rabbitmq_exchange_name,
                    routing_key=message.routing_key or f"shop.{message.event_name}",
                )
            except Exception as exc:
                await self.outbox_service.mark_failed(message, str(exc))
            else:
                await self.outbox_service.mark_published(message)

        await self.session.commit()
        return len(pending)
