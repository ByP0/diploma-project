from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated, Literal
from datetime import datetime
from uuid import UUID


class TokenPayload(BaseModel):
    sub: Annotated[
        UUID,
        Field(
            title="Subject",
            description="Unique identifier of the user (User ID)",
            examples=["550e8400-e29b-41d4-a716-446655440000"],
        ),
    ]

    type: Annotated[
        Literal["access", "refresh"],
        Field(
            title="Token type",
            description="Type of JWT token",
            examples=["access"],
        ),
    ]

    role: Annotated[
        str | None,
        Field(
            title="User role",
            description="Role of the user (included only in access token)",
            examples=["user"],
        ),
    ] = None

    exp: Annotated[
        datetime,
        Field(
            title="Expiration time",
            description="Token expiration timestamp",
            examples=["2024-01-01T12:30:00Z"],
        ),
    ]

    iat: Annotated[
        datetime,
        Field(
            title="Issued at",
            description="Token issued timestamp",
            examples=["2024-01-01T12:00:00Z"],
        ),
    ]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sub": "550e8400-e29b-41d4-a716-446655440000",
                "type": "access",
                "role": "user",
                "exp": "2024-01-01T12:30:00Z",
                "iat": "2024-01-01T12:00:00Z",
            }
        }
    )


class TokenPair(BaseModel):
    access_token: Annotated[
        str,
        Field(
            title="Access token",
            description="JWT access token",
            examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
        ),
    ]

    refresh_token: Annotated[
        str,
        Field(
            title="Refresh token",
            description="JWT refresh token",
            examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
        ),
    ]

    token_type: Annotated[
        str,
        Field(
            title="Token type",
            description="Authorization scheme",
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