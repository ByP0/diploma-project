from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import BOOLEAN, text
from sqlalchemy.dialects.postgresql import TEXT, TIMESTAMP, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseWithUUId


class UserRoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"
    SUPPORT = "support"


class User(BaseWithUUId):
    __tablename__ = "users"
    __allow_nullable__ = {
        "name",
        "avatar_image_id",
        "blocked_at",
        "blocked_reason",
        "email_verified_at",
        "password_reset_token_hash",
        "password_reset_expires_at",
        "password_reset_requested_at",
        "email_verification_token_hash",
        "email_verification_expires_at",
    }

    email: Mapped[str] = mapped_column(TEXT, unique=True)
    name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    avatar_image_id: Mapped[str | None] = mapped_column(VARCHAR(24), nullable=True)
    hashed_password: Mapped[str] = mapped_column(TEXT)
    role: Mapped[UserRoleEnum] = mapped_column(default=UserRoleEnum.USER)
    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, server_default=text("true"))
    is_blocked: Mapped[bool] = mapped_column(BOOLEAN, default=False, server_default=text("false"))
    blocked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(VARCHAR(500), nullable=True)
    email_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    password_reset_token_hash: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    password_reset_expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    password_reset_requested_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    email_verification_token_hash: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    email_verification_expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
