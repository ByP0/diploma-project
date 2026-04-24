from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB, INTEGER, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class AdminAuditLog(BaseWithUUId):
    __tablename__ = "admin_audit_logs"
    __is_updatable__ = False
    __allow_nullable__ = {
        "admin_user_id",
        "resource_id",
        "ip_address",
        "user_agent",
        "details",
    }
    __table_args__ = (
        Index("ix_admin_audit_logs_admin_user_id", "admin_user_id"),
        Index("ix_admin_audit_logs_action", "action"),
        Index("ix_admin_audit_logs_resource_type", "resource_type"),
        Index("ix_admin_audit_logs_created_at", "created_at"),
    )

    admin_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(VARCHAR(64))
    resource_type: Mapped[str] = mapped_column(VARCHAR(64))
    resource_id: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    request_method: Mapped[str] = mapped_column(VARCHAR(10))
    request_path: Mapped[str] = mapped_column(VARCHAR(255))
    status_code: Mapped[int] = mapped_column(INTEGER)
    ip_address: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(VARCHAR(512), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    admin_user = relationship(
        "User",
        foreign_keys=[admin_user_id],
        lazy="joined",
    )
