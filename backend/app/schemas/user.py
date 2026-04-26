from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator, model_validator

from app.core.images import build_image_url
from app.core.permissions import get_role_permissions
from app.models.user import UserRoleEnum


class UserBase(BaseModel):
    email: Annotated[EmailStr, Field(examples=["buyer@example.com"])]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserCreate(UserBase):
    password: Annotated[str, Field(min_length=8, max_length=128)]
    name: Annotated[str | None, Field(max_length=255)] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    model_config = ConfigDict(extra="forbid")


class UserLogin(BaseModel):
    email: Annotated[EmailStr, Field(examples=["buyer@example.com"])]
    password: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    model_config = ConfigDict(extra="forbid")


class UserPasswordRecoveryRequest(UserBase):
    model_config = ConfigDict(extra="forbid")


class UserPasswordReset(BaseModel):
    token: Annotated[str, Field(min_length=16, max_length=255)]
    new_password: Annotated[str, Field(min_length=8, max_length=128)]

    model_config = ConfigDict(extra="forbid")


class EmailVerificationStubRequest(UserBase):
    model_config = ConfigDict(extra="forbid")


class UserRead(UserBase):
    id: UUID
    name: str | None
    avatar_image_id: str | None
    role: UserRoleEnum
    is_active: bool
    is_blocked: bool
    blocked_at: datetime | None
    blocked_reason: str | None
    email_verified_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field(return_type=str | None)
    @property
    def avatar_url(self) -> str | None:
        if not self.avatar_image_id:
            return None
        return build_image_url(self.avatar_image_id)

    @computed_field(return_type=bool)
    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @computed_field(return_type=list[str])
    @property
    def permissions(self) -> list[str]:
        return sorted(permission.value for permission in get_role_permissions(self.role))

    model_config = ConfigDict(from_attributes=True)


class UserAdminUpdate(BaseModel):
    role: UserRoleEnum | None = None
    is_active: bool | None = None
    is_blocked: bool | None = None
    blocked_reason: Annotated[str | None, Field(max_length=500)] = None
    email_verified: bool | None = None

    @field_validator("blocked_reason")
    @classmethod
    def normalize_blocked_reason(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_blocking(self) -> "UserAdminUpdate":
        if self.is_blocked is False and self.blocked_reason:
            raise ValueError("blocked_reason can be set only when user is blocked")
        if self.is_blocked and not self.blocked_reason:
            self.blocked_reason = "Blocked by staff"
        return self

    model_config = ConfigDict(extra="forbid")


class UserProfileUpdate(BaseModel):
    name: Annotated[str | None, Field(max_length=255)] = None
    current_password: Annotated[str | None, Field(min_length=8, max_length=128)] = None
    new_password: Annotated[str | None, Field(min_length=8, max_length=128)] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be empty.")
        if len(normalized) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return normalized

    @model_validator(mode="after")
    def validate_password_change(self) -> "UserProfileUpdate":
        if self.new_password and not self.current_password:
            raise ValueError("Current password is required to change password.")
        if self.current_password and not self.new_password:
            raise ValueError("New password is required to change password.")
        return self

    model_config = ConfigDict(extra="forbid")


class UserLoginAuditRead(BaseModel):
    id: UUID
    user_id: UUID | None
    email: str
    event_type: str
    success: bool
    failure_reason: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
