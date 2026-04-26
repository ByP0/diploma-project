from __future__ import annotations

from collections import defaultdict

from app.events.event_bus.base import EventHandler


WILDCARD_EVENT = "*"


class EventHandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def register(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)

    def get_handlers(self, event_name: str) -> list[EventHandler]:
        return [*self._handlers.get(WILDCARD_EVENT, []), *self._handlers.get(event_name, [])]
