from __future__ import annotations

import enum

from sqlalchemy.dialects.postgresql import TEXT, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseWithUUId


class UserRoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(BaseWithUUId):
    __tablename__ = "users"
    __allow_nullable__ = {"name", "avatar_image_id"}

    email: Mapped[str] = mapped_column(TEXT, unique=True)
    name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    avatar_image_id: Mapped[str | None] = mapped_column(VARCHAR(24), nullable=True)
    hashed_password: Mapped[str] = mapped_column(TEXT)
    role: Mapped[UserRoleEnum] = mapped_column(default=UserRoleEnum.USER)
