from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, TEXT, TIMESTAMP, BOOLEAN

from datetime import datetime
from uuid import UUID

from app.models.base import BaseWithUUId


class RefreshToken(BaseWithUUId):
    __tablename__ = 'refresh_token'
    __is_updatable__ = False
    __table_args__ = (
        CheckConstraint("expires_at > created_at", name="ck_refresh_token_expires_after_create"),
        Index("ix_refresh_token_user_id", "user_id"),
        Index("ix_refresh_token_expires_at", "expires_at"),
        Index("ix_refresh_token_revoked", "revoked"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey('users.id', ondelete="CASCADE"),
    )
    hashed_token: Mapped[str] = mapped_column(TEXT)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))
    revoked: Mapped[bool] = mapped_column(BOOLEAN, default=False, server_default="false")
