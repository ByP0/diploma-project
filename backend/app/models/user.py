# app/models/user.py

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import TEXT
import enum

from app.models.base import BaseWithUUID

class UserRoleEnum(str, enum.Enum):
    USER = 'user'
    ADMIN = 'admin'

class User(BaseWithUUID):
    __tablename__ = 'users'

    email: Mapped[str] = mapped_column(TEXT, unique=True)
    hashed_password: Mapped[str] = mapped_column(TEXT)
    role: Mapped[UserRoleEnum] = mapped_column(default=UserRoleEnum.USER)
