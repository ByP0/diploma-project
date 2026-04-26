from __future__ import annotations

from app.events.event_bus.base import EventBus, EventContext
from app.events.event_bus.registry import EventHandlerRegistry
from app.events.schemas.envelope import BaseEvent
from app.events.subscribers.local_subscriber import build_event_handler_registry


class LocalEventBus(EventBus):
    def __init__(self, registry: EventHandlerRegistry | None = None) -> None:
        self.registry = registry or build_event_handler_registry()

    async def publish(self, event: BaseEvent, context: EventContext) -> None:
        for handler in self.registry.get_handlers(event.event_name):
            await handler(event, context)


_local_event_bus: LocalEventBus | None = None


def get_local_event_bus() -> LocalEventBus:
    global _local_event_bus
    if _local_event_bus is None:
        _local_event_bus = LocalEventBus()
    return _local_event_bus
