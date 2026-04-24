from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator, model_validator

from app.core.images import build_image_url
from app.models.user import UserRoleEnum


class UserBase(BaseModel):
    email: Annotated[
        EmailStr,
        Field(
            title="Электронная почта",
            description="Уникальный адрес электронной почты пользователя",
            examples=["buyer@example.com"],
        ),
    ]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserCreate(UserBase):
    password: Annotated[
        str,
        Field(
            title="Пароль",
            description="Пароль пользователя",
            examples=["Password1!"],
            min_length=8,
            max_length=128,
        ),
    ]

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "buyer@example.com",
                "password": "Password1!",
            }
        },
    )


class UserLogin(BaseModel):
    email: Annotated[
        EmailStr,
        Field(
            title="Электронная почта",
            description="Адрес электронной почты зарегистрированного пользователя",
            examples=["buyer@example.com"],
        ),
    ]
    password: Annotated[
        str,
        Field(
            title="Пароль",
            description="Пароль пользователя",
            examples=["Password1!"],
            min_length=8,
            max_length=128,
        ),
    ]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "email": "buyer@example.com",
                "password": "Password1!",
            }
        },
    )


class UserRead(UserBase):
    id: UUID
    name: str | None
    avatar_image_id: str | None
    role: UserRoleEnum
    created_at: datetime
    updated_at: datetime

    @computed_field(
        return_type=str | None,
        title="Ссылка на аватар",
        description="Готовая ссылка для отображения аватарки пользователя",
    )
    @property
    def avatar_url(self) -> str | None:
        if not self.avatar_image_id:
            return None
        return build_image_url(self.avatar_image_id)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "buyer@example.com",
                "name": "Иван Иванов",
                "avatar_image_id": "6622eacaf2f4b22a4eb8ac11",
                "avatar_url": "/api/images/6622eacaf2f4b22a4eb8ac11",
                "role": "user",
                "created_at": "2026-04-23T12:00:00Z",
                "updated_at": "2026-04-23T12:30:00Z",
            }
        },
    )


class UserProfileUpdate(BaseModel):
    name: Annotated[
        str | None,
        Field(
            title="Имя",
            description="Отображаемое имя пользователя",
            max_length=255,
            examples=["Иван Иванов"],
        ),
    ] = None
    current_password: Annotated[
        str | None,
        Field(
            title="Текущий пароль",
            description="Текущий пароль пользователя для подтверждения смены пароля",
            min_length=8,
            max_length=128,
        ),
    ] = None
    new_password: Annotated[
        str | None,
        Field(
            title="Новый пароль",
            description="Новый пароль пользователя",
            min_length=8,
            max_length=128,
            examples=["NewPassword1!"],
        ),
    ] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Имя не должно быть пустым.")
        if len(normalized) < 2:
            raise ValueError("Имя должно содержать минимум 2 символа.")
        return normalized

    @model_validator(mode="after")
    def validate_password_change(self) -> "UserProfileUpdate":
        if self.new_password and not self.current_password:
            raise ValueError("Для смены пароля нужно указать текущий пароль.")
        if self.current_password and not self.new_password:
            raise ValueError("Укажите новый пароль для завершения смены пароля.")
        return self

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Иван Иванов",
                "current_password": "Password1!",
                "new_password": "NewPassword1!",
            }
        },
    )
