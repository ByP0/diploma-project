"""add support center entities

Revision ID: e8f5b7c1a201
Revises: d91a6c4b7e12
Create Date: 2026-04-24 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e8f5b7c1a201"
down_revision: Union[str, Sequence[str], None] = "d91a6c4b7e12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    support_ticket_status_enum = postgresql.ENUM(
        "OPEN",
        "IN_PROGRESS",
        "WAITING_CUSTOMER",
        "RESOLVED",
        "CLOSED",
        name="supportticketstatusenum",
        create_type=False,
    )
    support_ticket_priority_enum = postgresql.ENUM(
        "LOW",
        "NORMAL",
        "HIGH",
        "URGENT",
        name="supportticketpriorityenum",
        create_type=False,
    )
    support_message_author_enum = postgresql.ENUM(
        "CUSTOMER",
        "AI",
        "ADMIN",
        name="supportmessageauthorenum",
        create_type=False,
    )
    support_ticket_status_enum.create(op.get_bind(), checkfirst=True)
    support_ticket_priority_enum.create(op.get_bind(), checkfirst=True)
    support_message_author_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "support_tickets",
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("assigned_admin_id", sa.UUID(), nullable=True),
        sa.Column("contact_email", sa.TEXT(), nullable=True),
        sa.Column("subject", sa.VARCHAR(length=200), nullable=False),
        sa.Column("status", support_ticket_status_enum, nullable=False, server_default="OPEN"),
        sa.Column("priority", support_ticket_priority_enum, nullable=False, server_default="NORMAL"),
        sa.Column(
            "human_handoff_requested",
            sa.BOOLEAN(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "ai_last_used",
            sa.BOOLEAN(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "last_message_preview",
            sa.VARCHAR(length=280),
            nullable=False,
            server_default=sa.text("''"),
        ),
        sa.Column("last_customer_message_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_admin_reply_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assigned_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"], unique=False)
    op.create_index("ix_support_tickets_priority", "support_tickets", ["priority"], unique=False)
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"], unique=False)
    op.create_index(
        "ix_support_tickets_assigned_admin_id",
        "support_tickets",
        ["assigned_admin_id"],
        unique=False,
    )
    op.create_index(
        "ix_support_tickets_human_handoff_requested",
        "support_tickets",
        ["human_handoff_requested"],
        unique=False,
    )

    op.create_table(
        "support_messages",
        sa.Column("ticket_id", sa.UUID(), nullable=False),
        sa.Column("author_type", support_message_author_enum, nullable=False),
        sa.Column("author_user_id", sa.UUID(), nullable=True),
        sa.Column("author_name", sa.VARCHAR(length=255), nullable=True),
        sa.Column("body", sa.TEXT(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["ticket_id"], ["support_tickets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_support_messages_ticket_id", "support_messages", ["ticket_id"], unique=False)
    op.create_index(
        "ix_support_messages_author_type",
        "support_messages",
        ["author_type"],
        unique=False,
    )
    op.create_index(
        "ix_support_messages_author_user_id",
        "support_messages",
        ["author_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_support_messages_author_user_id", table_name="support_messages")
    op.drop_index("ix_support_messages_author_type", table_name="support_messages")
    op.drop_index("ix_support_messages_ticket_id", table_name="support_messages")
    op.drop_table("support_messages")

    op.drop_index(
        "ix_support_tickets_human_handoff_requested",
        table_name="support_tickets",
    )
    op.drop_index("ix_support_tickets_assigned_admin_id", table_name="support_tickets")
    op.drop_index("ix_support_tickets_user_id", table_name="support_tickets")
    op.drop_index("ix_support_tickets_priority", table_name="support_tickets")
    op.drop_index("ix_support_tickets_status", table_name="support_tickets")
    op.drop_table("support_tickets")

    postgresql.ENUM(name="supportmessageauthorenum").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="supportticketpriorityenum").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="supportticketstatusenum").drop(op.get_bind(), checkfirst=True)
