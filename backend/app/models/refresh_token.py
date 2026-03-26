# app/models/refresh_token.py

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import TEXT, TIMESTAMP, BOOLEAN
from datetime import datetime
import uuid

from app.models.base import BaseWithUUID

class RefreshToken(BaseWithUUID):
    __tablename__ = 'refresh_tokens'
    __is_updatable__ = False

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('users.id'))
    hashed_token: Mapped[str] = mapped_column(TEXT)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    revoked: Mapped[bool] = mapped_column(BOOLEAN, default=False)
