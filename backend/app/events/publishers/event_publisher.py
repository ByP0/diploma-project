from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import setting
from app.events.event_bus.base import EventContext
from app.events.event_bus.local_bus import get_local_event_bus
from app.events.outbox.service import OutboxService
from app.events.schemas.envelope import DomainEvent, IntegrationEvent
from app.observability.context import get_correlation_id, get_request_id


class EventPublisher:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.outbox_service = OutboxService(session)
        self.local_bus = get_local_event_bus()

    async def publish_domain(
        self,
        event: DomainEvent,
        *,
        dispatch_immediately: bool | None = None,
    ) -> None:
        if not setting.events_enabled:
            return

        envelope = self._enrich_envelope(event.to_envelope())
        message = await self.outbox_service.record(
            envelope,
            destination="local",
            status="pending",
        )

        immediate = setting.events_dispatch_immediately if dispatch_immediately is None else dispatch_immediately
        if not immediate:
            return

        try:
            await self.outbox_service.mark_processing(message)
            await self.local_bus.publish(
                event,
                EventContext(
                    session=self.session,
                    publisher=self,
                    metadata={key: str(value) for key, value in envelope.metadata.items()},
                ),
            )
        except Exception as exc:
            await self.outbox_service.mark_failed(message, str(exc))
            raise
        else:
            await self.outbox_service.mark_processed(message)

    async def publish_integration(
        self,
        event: IntegrationEvent,
        *,
        routing_key: str | None = None,
        exchange_name: str | None = None,
    ) -> None:
        if not setting.events_enabled:
            return

        envelope = self._enrich_envelope(event.to_envelope())
        await self.outbox_service.record(
            envelope,
            destination="broker",
            status="pending",
            exchange_name=exchange_name or setting.events_rabbitmq_exchange_name,
            routing_key=routing_key or f"shop.{event.event_name}",
        )

    @staticmethod
    def _enrich_envelope(envelope):
        correlation_id = envelope.correlation_id or get_correlation_id() or get_request_id() or str(envelope.event_id)
        if "correlation_id" not in envelope.metadata:
            envelope.metadata["correlation_id"] = correlation_id
        if envelope.correlation_id is None:
            envelope.correlation_id = correlation_id
        return envelope
