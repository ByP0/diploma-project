from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.support_message import SupportMessageAuthorEnum
from app.models.support_ticket import (
    SupportTicketPriorityEnum,
    SupportTicketStatusEnum,
)


class SupportMessageRead(BaseModel):
    id: UUID
    author_type: SupportMessageAuthorEnum
    author_name: str | None
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupportTicketSummary(BaseModel):
    id: UUID
    subject: str
    status: SupportTicketStatusEnum
    priority: SupportTicketPriorityEnum
    contact_email: str | None
    human_handoff_requested: bool
    ai_last_used: bool
    last_message_preview: str
    last_customer_message_at: datetime | None
    last_admin_reply_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupportTicketRead(SupportTicketSummary):
    assigned_admin_id: UUID | None
    messages: list[SupportMessageRead]

    model_config = ConfigDict(from_attributes=True)


class SupportAdminReplyCreate(BaseModel):
    message: Annotated[
        str,
        Field(
            title="Ответ администратора",
            description="Текст ответа покупателю от лица администратора или оператора поддержки",
            min_length=1,
            max_length=4000,
        ),
    ]
    status: Annotated[
        SupportTicketStatusEnum | None,
        Field(
            title="Новый статус",
            description="Статус обращения после ответа администратора",
        ),
    ] = None

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Сообщение администратора не должно быть пустым.")
        return value

    model_config = ConfigDict(extra="forbid")


class SupportTicketAdminUpdate(BaseModel):
    status: Annotated[
        SupportTicketStatusEnum | None,
        Field(
            title="Статус",
            description="Новый статус обращения",
        ),
    ] = None
    priority: Annotated[
        SupportTicketPriorityEnum | None,
        Field(
            title="Приоритет",
            description="Приоритет обработки обращения",
        ),
    ] = None
    assigned_admin_id: Annotated[
        UUID | None,
        Field(
            title="Назначенный администратор",
            description="Идентификатор администратора, который ведет обращение",
        ),
    ] = None

    model_config = ConfigDict(extra="forbid")


class SupportTicketListResponse(BaseModel):
    items: list[SupportTicketSummary]
