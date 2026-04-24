from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.support_ticket import SupportTicketStatusEnum


class ChatRequest(BaseModel):
    message: Annotated[
        str,
        Field(
            title="РЎРѕРѕР±С‰РµРЅРёРµ",
            description="Р’РѕРїСЂРѕСЃ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ Рє Р±РѕС‚Сѓ РїРѕРґРґРµСЂР¶РєРё",
            min_length=1,
            max_length=2000,
            examples=["РљР°РєРёРµ С‚РѕРІР°СЂС‹ РµСЃС‚СЊ РІ РЅР°Р»РёС‡РёРё Рё РµСЃС‚СЊ Р»Рё Сѓ РјРµРЅСЏ Р°РєС‚РёРІРЅС‹Рµ Р·Р°РєР°Р·С‹?"],
        ),
    ]
    ticket_id: Annotated[
        UUID | None,
        Field(
            title="Обращение",
            description="Идентификатор существующего обращения, если нужно продолжить диалог в том же треде поддержки",
        ),
    ] = None
    contact_email: Annotated[
        EmailStr | None,
        Field(
            title="Контактный email",
            description="Контактная почта гостя для привязки обращения без авторизации",
        ),
    ] = None
    request_human: Annotated[
        bool,
        Field(
            title="Передать оператору",
            description="Если включено, обращение будет помечено для обработки человеком",
        ),
    ] = False

    @field_validator("message")
    @classmethod
    def normalize_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("РЎРѕРѕР±С‰РµРЅРёРµ РЅРµ РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ РїСѓСЃС‚С‹Рј.")
        return value

    @field_validator("contact_email")
    @classmethod
    def normalize_optional_email(cls, value: EmailStr | None) -> str | None:
        if value is None:
            return value
        return str(value).strip().lower()

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "message": "РљР°РєРёРµ С‚РѕРІР°СЂС‹ РµСЃС‚СЊ РІ РЅР°Р»РёС‡РёРё Рё РµСЃС‚СЊ Р»Рё Сѓ РјРµРЅСЏ Р°РєС‚РёРІРЅС‹Рµ Р·Р°РєР°Р·С‹?",
                "request_human": False,
            }
        },
    )


class ChatResponse(BaseModel):
    answer: str
    used_ai: bool
    used_user_context: bool
    ticket_id: UUID
    ticket_status: SupportTicketStatusEnum
    human_handoff_requested: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "РЎРµР№С‡Р°СЃ РІ РЅР°Р»РёС‡РёРё РµСЃС‚СЊ Р±Р°РЅР°РЅС‹ Рё РјРѕР»РѕРєРѕ. РЈ РІР°СЃ РµСЃС‚СЊ РѕРґРёРЅ Р·Р°РєР°Р· СЃРѕ СЃС‚Р°С‚СѓСЃРѕРј В«РІ РѕР±СЂР°Р±РѕС‚РєРµВ».",
                "used_ai": True,
                "used_user_context": True,
                "ticket_id": "550e8400-e29b-41d4-a716-446655440000",
                "ticket_status": "open",
                "human_handoff_requested": False,
            }
        }
    )
