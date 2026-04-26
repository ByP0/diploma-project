from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Awaitable, Callable, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.events.schemas.envelope import BaseEvent

if TYPE_CHECKING:
    from app.events.publishers.event_publisher import EventPublisher


EventHandler = Callable[[BaseEvent, "EventContext"], Awaitable[None]]


@dataclass(slots=True)
class EventContext:
    session: AsyncSession
    publisher: "EventPublisher"
    metadata: dict[str, str] = field(default_factory=dict)


class EventBus(Protocol):
    async def publish(self, event: BaseEvent, context: EventContext) -> None:
        ...
