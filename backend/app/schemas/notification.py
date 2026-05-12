from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationMessageRead(BaseModel):
    id: UUID
    channel: str
    template_name: str
    recipient: str
    subject: str
    body_text: str
    body_html: str | None
    context_payload: dict[str, object] | None
    status: str
    attempts: int
    max_attempts: int
    provider_name: str | None
    last_error: str | None
    next_retry_at: datetime | None
    sent_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
