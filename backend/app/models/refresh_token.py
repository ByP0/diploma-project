from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, TEXT, TIMESTAMP, BOOLEAN

from datetime import datetime
import uuid

from app.models.base import BaseWithUUId


class RefreshToken(BaseWithUUId):
    __tablename__ = 'refresh_token'
    __is_updatable__ = False

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'))
    hashed_token: Mapped[str] = mapped_column(TEXT)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    revoked: Mapped[bool] = mapped_column(BOOLEAN, default=False)