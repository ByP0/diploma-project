from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import BOOLEAN, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class UserLoginAuditLog(BaseWithUUId):
    __tablename__ = "user_login_audit_logs"
    __is_updatable__ = False
    __allow_nullable__ = {
        "user_id",
        "failure_reason",
        "ip_address",
        "user_agent",
        "details",
    }
    __table_args__ = (
        Index("ix_user_login_audit_logs_user_id", "user_id"),
        Index("ix_user_login_audit_logs_email", "email"),
        Index("ix_user_login_audit_logs_success", "success"),
        Index("ix_user_login_audit_logs_created_at", "created_at"),
    )

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    email: Mapped[str] = mapped_column(VARCHAR(255))
    event_type: Mapped[str] = mapped_column(VARCHAR(32), default="login", server_default="login")
    success: Mapped[bool] = mapped_column(BOOLEAN)
    failure_reason: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(VARCHAR(512), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user = relationship("User", lazy="joined")
