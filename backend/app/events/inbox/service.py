from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import setting
from app.events.event_bus.transition_logger import log_event_transition
from app.events.inbox.models import InboxMessage


class InboxService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def acquire(
        self,
        *,
        event_id: UUID,
        event_name: str,
        source: str,
        consumer_name: str,
        payload: dict,
        correlation_id: str | None = None,
    ) -> InboxMessage | None:
        result = await self.session.execute(
            select(InboxMessage).where(
                InboxMessage.event_id == event_id,
                InboxMessage.consumer_name == consumer_name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.status in {"processed", "dead_letter", "processing"}:
                return None
            previous_status = existing.status
            existing.status = "processing"
            existing.last_error = None
            existing.attempts += 1
            log_event_transition(
                entity="inbox",
                message_id=str(existing.id),
                event_name=existing.event_name,
                from_status=previous_status,
                to_status=existing.status,
                correlation_id=existing.correlation_id,
                extra_payload={"consumer_name": existing.consumer_name, "attempts": existing.attempts},
            )
            if hasattr(self.session, "flush"):
                await self.session.flush()
            return existing

        message = InboxMessage(
            event_id=event_id,
            event_name=event_name,
            source=source,
            consumer_name=consumer_name,
            correlation_id=correlation_id,
            payload=payload,
            status="processing",
            attempts=1,
            max_attempts=setting.events_inbox_max_attempts,
        )
        self.session.add(message)
        if hasattr(self.session, "flush"):
            await self.session.flush()
        log_event_transition(
            entity="inbox",
            message_id=str(message.id),
            event_name=message.event_name,
            from_status=None,
            to_status=message.status,
            correlation_id=message.correlation_id,
            extra_payload={"consumer_name": message.consumer_name, "attempts": message.attempts},
        )
        return message

    async def mark_processed(self, message: InboxMessage) -> None:
        previous_status = message.status
        message.status = "processed"
        message.processed_at = datetime.now(timezone.utc)
        message.last_error = None
        log_event_transition(
            entity="inbox",
            message_id=str(message.id),
            event_name=message.event_name,
            from_status=previous_status,
            to_status=message.status,
            correlation_id=message.correlation_id,
            extra_payload={"consumer_name": message.consumer_name},
        )

    async def mark_failed(self, message: InboxMessage, error: str) -> bool:
        previous_status = message.status
        message.last_error = error[:1000]
        if message.attempts >= message.max_attempts:
            message.status = "dead_letter"
            message.dead_lettered_at = datetime.now(timezone.utc)
            log_event_transition(
                entity="inbox",
                message_id=str(message.id),
                event_name=message.event_name,
                from_status=previous_status,
                to_status=message.status,
                correlation_id=message.correlation_id,
                extra_payload={"consumer_name": message.consumer_name, "attempts": message.attempts},
            )
            return False

        message.status = "failed"
        log_event_transition(
            entity="inbox",
            message_id=str(message.id),
            event_name=message.event_name,
            from_status=previous_status,
            to_status=message.status,
            correlation_id=message.correlation_id,
            extra_payload={"consumer_name": message.consumer_name, "attempts": message.attempts},
        )
        return True
