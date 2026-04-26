from __future__ import annotations

import logging
from typing import Any

from app.observability.metrics import metrics_registry


logger = logging.getLogger(__name__)


def log_event_transition(
    *,
    entity: str,
    message_id: str,
    event_name: str,
    from_status: str | None,
    to_status: str,
    correlation_id: str | None = None,
    extra_payload: dict[str, Any] | None = None,
) -> None:
    metrics_registry.increment(
        "shop_event_transitions_total",
        entity=entity,
        event_name=event_name,
        status=to_status,
    )
    logger.info(
        "event_transition",
        extra={
            "event": "event_transition",
            "entity": entity,
            "message_id": message_id,
            "event_name": event_name,
            "from_status": from_status,
            "to_status": to_status,
            "correlation_id": correlation_id,
            **(extra_payload or {}),
        },
    )
