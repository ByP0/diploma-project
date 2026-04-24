import enum
from uuid import UUID

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import TEXT, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class SupportMessageAuthorEnum(str, enum.Enum):
    CUSTOMER = "customer"
    AI = "ai"
    ADMIN = "admin"


class SupportMessage(BaseWithUUId):
    __tablename__ = "support_messages"
    __table_args__ = (
        Index("ix_support_messages_ticket_id", "ticket_id"),
        Index("ix_support_messages_author_type", "author_type"),
        Index("ix_support_messages_author_user_id", "author_user_id"),
    )

    ticket_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
    )
    author_type: Mapped[SupportMessageAuthorEnum]
    author_user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    author_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    body: Mapped[str] = mapped_column(TEXT)

    ticket = relationship(
        "SupportTicket",
        back_populates="messages",
        lazy="joined",
    )
    author_user = relationship(
        "User",
        foreign_keys=[author_user_id],
        lazy="joined",
    )
