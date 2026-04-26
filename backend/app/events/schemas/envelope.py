from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, ClassVar
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


_EVENT_MODEL_REGISTRY: dict[str, type["BaseEvent"]] = {}


class EventKindEnum(str, enum.Enum):
    DOMAIN = "domain"
    INTEGRATION = "integration"


class EventEnvelope(BaseModel):
    event_id: UUID
    event_name: str
    event_kind: EventKindEnum
    version: int
    correlation_id: str | None = None
    causation_id: str | None = None
    aggregate_type: str
    aggregate_id: str | None
    occurred_at: datetime
    payload: dict[str, Any]
    metadata: dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class BaseEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)

    __event_version__: ClassVar[int] = 1
    __aggregate_type__: ClassVar[str] = "generic"
    __aggregate_id_field__: ClassVar[str | None] = None
    __event_kind__: ClassVar[EventKindEnum] = EventKindEnum.DOMAIN

    model_config = ConfigDict(extra="forbid")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__name__ not in {"BaseEvent", "DomainEvent", "IntegrationEvent"}:
            _EVENT_MODEL_REGISTRY[cls.__name__] = cls

    @property
    def event_name(self) -> str:
        return self.__class__.__name__

    @property
    def aggregate_type(self) -> str:
        return self.__class__.__aggregate_type__

    @property
    def aggregate_id(self) -> str | None:
        if not self.__class__.__aggregate_id_field__:
            return None
        value = getattr(self, self.__class__.__aggregate_id_field__, None)
        return None if value is None else str(value)

    @property
    def event_kind(self) -> EventKindEnum:
        return self.__class__.__event_kind__

    def to_envelope(self) -> EventEnvelope:
        return EventEnvelope(
            event_id=self.event_id,
            event_name=self.event_name,
            event_kind=self.event_kind,
            version=self.__class__.__event_version__,
            correlation_id=self.metadata.get("correlation_id"),
            causation_id=self.metadata.get("causation_id"),
            aggregate_type=self.aggregate_type,
            aggregate_id=self.aggregate_id,
            occurred_at=self.occurred_at,
            payload=self.model_dump(mode="json"),
            metadata=self.metadata,
        )


class DomainEvent(BaseEvent):
    __event_kind__ = EventKindEnum.DOMAIN


class IntegrationEvent(BaseEvent):
    __event_kind__ = EventKindEnum.INTEGRATION


def get_event_model(event_name: str) -> type[BaseEvent]:
    event_model = _EVENT_MODEL_REGISTRY.get(event_name)
    if event_model is None:
        raise ValueError(f"Unknown event model '{event_name}'.")
    return event_model


def event_from_envelope(value: EventEnvelope | dict[str, Any]) -> BaseEvent:
    envelope = value if isinstance(value, EventEnvelope) else EventEnvelope.model_validate(value)
    event_model = get_event_model(envelope.event_name)
    return event_model.model_validate(envelope.payload)
