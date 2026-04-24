from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated, Literal
from datetime import datetime
from uuid import UUID


class TokenPayload(BaseModel):
    sub: Annotated[
        UUID,
        Field(
            title="Пользователь",
            description="Идентификатор пользователя, которому принадлежит токен",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        ),
    ]

    type: Annotated[
        Literal["access", "refresh"],
        Field(
            title="Тип токена",
            description="Тип токена",
            examples=["access"],
        ),
    ]

    role: Annotated[
        str | None,
        Field(
            title="Роль",
            description="Роль пользователя, присутствует только в токене доступа",
            examples=["user"],
        ),
    ] = None

    exp: Annotated[
        datetime,
        Field(
            title="Срок действия",
            description="Дата и время окончания действия токена",
            examples=["2026-04-23T12:30:00Z"],
        ),
    ]

    iat: Annotated[
        datetime,
        Field(
            title="Дата выдачи",
            description="Дата и время создания токена",
            examples=["2026-04-23T12:00:00Z"],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "550e8400-e29b-41d4-a716-446655440000",
                "type": "access",
                "role": "user",
                "exp": "2026-04-23T12:30:00Z",
                "iat": "2026-04-23T12:00:00Z",
            }
        }
    )


class TokenPair(BaseModel):
    access_token: Annotated[
        str,
        Field(
            title="Токен доступа",
            description="Токен доступа",
            examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
        ),
    ]

    refresh_token: Annotated[
        str,
        Field(
            title="Токен обновления",
            description="Токен обновления",
            examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
        ),
    ]

    token_type: Annotated[
        str,
        Field(
            title="Схема авторизации",
            description="Тип токена для заголовка авторизации",
            examples=["bearer"],
        ),
    ] = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )
