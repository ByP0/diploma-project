from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Annotated
from datetime import datetime
import uuid

from app.models.user import UserRoleEnum
from app.core.security import pattern_password


class UserBase(BaseModel):
    email: Annotated[
        EmailStr,
        Field(
            title="User email",
            description="Unique email address of the user",
            examples=["example@gmail.com"],
        ),
]


class UserCreate(UserBase):
    password: Annotated[
        str,
        Field(
            title="Password",
            description="User password (must match security policy)",
            pattern=pattern_password,
            examples=["Password1!"],
            min_length=8,
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "example@gmail.com",
                "password": "Password1!",
            }
        }
    )


class UserLogin(BaseModel):
    email: Annotated[
        EmailStr,
        Field(
            title="User email",
            examples=["example@gmail.com"],
        ),
    ]

    password: Annotated[
        str,
        Field(
            title="Password",
            examples=["Password1!"],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "example@gmail.com",
                "password": "Password1!",
            }
        }
    )


class UserRead(UserBase):
    id: Annotated[
        uuid.UUID,
        Field(
            title="User ID",
            description="Unique identifier of the user",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        ),
    ]

    role: Annotated[
        UserRoleEnum,
        Field(
            title="User role",
            description="Role assigned to the user",
            examples=["user"],
        ),
    ]

    created_at: Annotated[
        datetime,
        Field(
            title="Created at",
            description="Timestamp when the user was created",
            examples=["2024-01-01T12:00:00Z"],
        ),
    ]

    updated_at: Annotated[
        datetime,
        Field(
            title="Updated at",
            description="Timestamp when the user was last updated",
            examples=["2024-01-02T15:30:00Z"],
        ),
    ]

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "example@gmail.com",
                "role": "user",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-02T15:30:00Z",
            }
        },
    )


class UserUpdate(BaseModel):
    email: Annotated[
        EmailStr | None,
        Field(
            title="New email",
            examples=["new@example.com"],
        ),
    ] = None

    password: Annotated[
        str | None,
        Field(
            title="New password",
            pattern=pattern_password,
            examples=["NewPassword1!"],
        ),
    ] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "new@example.com",
                "password": "NewPassword1!",
            }
        }
    )