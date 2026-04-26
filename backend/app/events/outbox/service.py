from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import setting
from app.events.event_bus.transition_logger import log_event_transition
from app.events.outbox.models import OutboxMessage
from app.events.schemas.envelope import EventEnvelope


class OutboxService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        envelope: EventEnvelope,
        *,
        destination: str,
        status: str,
        exchange_name: str | None = None,
        routing_key: str | None = None,
    ) -> OutboxMessage:
        message = OutboxMessage(
            event_id=envelope.event_id,
            event_name=envelope.event_name,
            event_kind=envelope.event_kind.value,
            aggregate_type=envelope.aggregate_type,
            aggregate_id=envelope.aggregate_id,
            version=envelope.version,
            correlation_id=envelope.correlation_id,
            causation_id=envelope.causation_id,
            payload=envelope.payload,
            headers=envelope.metadata,
            status=status,
            destination=destination,
            attempts=0,
            max_attempts=setting.events_outbox_max_attempts,
            exchange_name=exchange_name,
            routing_key=routing_key,
        )
        self.session.add(message)
        if hasattr(self.session, "flush"):
            await self.session.flush()
        log_event_transition(
            entity="outbox",
            message_id=str(message.id),
            event_name=message.event_name,
            from_status=None,
            to_status=message.status,
            correlation_id=message.correlation_id,
            extra_payload={"destination": destination},
        )
        return message

    async def list_pending(self, *, destination: str, limit: int = 100) -> list[OutboxMessage]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(OutboxMessage)
            .where(
                OutboxMessage.destination == destination,
                OutboxMessage.status.in_(["pending", "retrying"]),
                ((OutboxMessage.next_retry_at.is_(None)) | (OutboxMessage.next_retry_at <= now)),
            )
            .order_by(OutboxMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_processing(self, message: OutboxMessage) -> None:
        previous_status = message.status
        message.status = "processing"
        log_event_transition(
            entity="outbox",
            message_id=str(message.id),
            event_name=message.event_name,
            from_status=previous_status,
            to_status=message.status,
            correlation_id=message.correlation_id,
        )

    async def mark_processed(self, message: OutboxMessage) -> None:
        previous_status = message.status
        message.status = "processed"
        message.processed_at = datetime.now(timezone.utc)
        message.next_retry_at = None
        message.last_error = None
        log_event_transition(
            entity="outbox",
            message_id=str(message.id),
            event_name=message.event_name,
            from_status=previous_status,
            to_status=message.status,
            correlation_id=message.correlation_id,
        )

    async def mark_published(self, message: OutboxMessage) -> None:
        previous_status = message.status
        message.status = "published"
        message.published_at = datetime.now(timezone.utc)
        message.next_retry_at = None
        message.last_error = None
        log_event_transition(
            entity="outbox",
            message_id=str(message.id),
            event_name=message.event_name,
            from_status=previous_status,
            to_status=message.status,
            correlation_id=message.correlation_id,
        )

    async def mark_failed(self, message: OutboxMessage, error: str) -> bool:
        previous_status = message.status
        message.attempts += 1
        message.last_error = error[:1000]
        if message.attempts >= message.max_attempts:
            message.status = "dead_letter"
            message.dead_lettered_at = datetime.now(timezone.utc)
            message.next_retry_at = None
            log_event_transition(
                entity="outbox",
                message_id=str(message.id),
                event_name=message.event_name,
                from_status=previous_status,
                to_status=message.status,
                correlation_id=message.correlation_id,
                extra_payload={"attempts": message.attempts},
            )
            return False

        message.status = "retrying"
        message.next_retry_at = datetime.now(timezone.utc) + timedelta(
            seconds=setting.events_retry_base_delay_seconds * max(1, message.attempts)
        )
        log_event_transition(
            entity="outbox",
            message_id=str(message.id),
            event_name=message.event_name,
            from_status=previous_status,
            to_status=message.status,
            correlation_id=message.correlation_id,
            extra_payload={"attempts": message.attempts},
        )
        return True
