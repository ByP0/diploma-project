import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import BOOLEAN, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import TEXT, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class SupportTicketStatusEnum(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportTicketPriorityEnum(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicket(BaseWithUUId):
    __tablename__ = "support_tickets"
    __table_args__ = (
        Index("ix_support_tickets_status", "status"),
        Index("ix_support_tickets_priority", "priority"),
        Index("ix_support_tickets_user_id", "user_id"),
        Index("ix_support_tickets_assigned_admin_id", "assigned_admin_id"),
        Index(
            "ix_support_tickets_human_handoff_requested",
            "human_handoff_requested",
        ),
    )

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_admin_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    contact_email: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    subject: Mapped[str] = mapped_column(VARCHAR(200))
    status: Mapped[SupportTicketStatusEnum] = mapped_column(
        default=SupportTicketStatusEnum.OPEN,
        server_default=SupportTicketStatusEnum.OPEN.name,
    )
    priority: Mapped[SupportTicketPriorityEnum] = mapped_column(
        default=SupportTicketPriorityEnum.NORMAL,
        server_default=SupportTicketPriorityEnum.NORMAL.name,
    )
    human_handoff_requested: Mapped[bool] = mapped_column(
        BOOLEAN,
        default=False,
        server_default=text("false"),
    )
    ai_last_used: Mapped[bool] = mapped_column(
        BOOLEAN,
        default=False,
        server_default=text("false"),
    )
    last_message_preview: Mapped[str] = mapped_column(
        VARCHAR(280),
        default="",
        server_default=text("''"),
    )
    last_customer_message_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    last_admin_reply_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    requester = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="joined",
    )
    assigned_admin = relationship(
        "User",
        foreign_keys=[assigned_admin_id],
        lazy="joined",
    )
    messages = relationship(
        "SupportMessage",
        cascade="all, delete-orphan",
        back_populates="ticket",
        lazy="selectin",
        order_by="SupportMessage.created_at",
    )
