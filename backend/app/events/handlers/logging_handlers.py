from __future__ import annotations

import logging

from app.events.event_bus.base import EventContext
from app.events.schemas.envelope import BaseEvent


logger = logging.getLogger(__name__)


async def log_event(event: BaseEvent, _context: EventContext) -> None:
    logger.info(
        "event_emitted",
        extra={
            "event": "event_emitted",
            "event_name": event.event_name,
            "event_kind": event.event_kind.value,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
        },
    )
