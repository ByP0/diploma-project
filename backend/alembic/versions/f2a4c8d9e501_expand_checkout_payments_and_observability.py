"""expand checkout payments and observability

Revision ID: f2a4c8d9e501
Revises: e8f5b7c1a201
Create Date: 2026-04-24 14:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f2a4c8d9e501"
down_revision: Union[str, Sequence[str], None] = "e8f5b7c1a201"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    delivery_method_enum = postgresql.ENUM(
        "COURIER",
        "EXPRESS",
        "PICKUP",
        name="deliverymethodenum",
        create_type=False,
    )
    payment_method_enum = postgresql.ENUM(
        "CARD_ONLINE",
        "CASH_ON_DELIVERY",
        "CARD_ON_DELIVERY",
        name="paymentmethodenum",
        create_type=False,
    )
    payment_status_enum = postgresql.ENUM(
        "PENDING",
        "SUCCEEDED",
        "FAILED",
        "CANCELLED",
        name="paymentstatusenum",
        create_type=False,
    )

    delivery_method_enum.create(op.get_bind(), checkfirst=True)
    payment_method_enum.create(op.get_bind(), checkfirst=True)
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'CANCELLED'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'CONFIRMED'")
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'OUT_FOR_DELIVERY'")

    op.add_column("orders", sa.Column("customer_email", sa.VARCHAR(length=255), nullable=True))
    op.add_column("orders", sa.Column("customer_name", sa.VARCHAR(length=255), nullable=True))
    op.add_column("orders", sa.Column("customer_phone", sa.VARCHAR(length=32), nullable=True))
    op.add_column("orders", sa.Column("customer_comment", sa.VARCHAR(length=1000), nullable=True))
    op.add_column(
        "orders",
        sa.Column(
            "delivery_method",
            delivery_method_enum,
            nullable=False,
            server_default="COURIER",
        ),
    )
    op.add_column(
        "orders",
        sa.Column("delivery_window_start", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("delivery_window_end", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column("orders", sa.Column("delivery_address_line1", sa.VARCHAR(length=255), nullable=True))
    op.add_column("orders", sa.Column("delivery_address_line2", sa.VARCHAR(length=255), nullable=True))
    op.add_column("orders", sa.Column("delivery_city", sa.VARCHAR(length=128), nullable=True))
    op.add_column("orders", sa.Column("delivery_region", sa.VARCHAR(length=128), nullable=True))
    op.add_column("orders", sa.Column("delivery_postal_code", sa.VARCHAR(length=32), nullable=True))
    op.add_column(
        "orders",
        sa.Column("delivery_country", sa.VARCHAR(length=2), nullable=False, server_default="RU"),
    )
    op.add_column("orders", sa.Column("delivery_floor", sa.VARCHAR(length=32), nullable=True))
    op.add_column("orders", sa.Column("delivery_apartment", sa.VARCHAR(length=32), nullable=True))
    op.add_column("orders", sa.Column("delivery_entrance", sa.VARCHAR(length=32), nullable=True))
    op.add_column("orders", sa.Column("delivery_intercom", sa.VARCHAR(length=64), nullable=True))
    op.add_column("orders", sa.Column("delivery_instructions", sa.VARCHAR(length=1000), nullable=True))
    op.add_column(
        "orders",
        sa.Column(
            "payment_method",
            payment_method_enum,
            nullable=False,
            server_default="CARD_ONLINE",
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "payment_status",
            payment_status_enum,
            nullable=False,
            server_default="PENDING",
        ),
    )
    op.add_column(
        "orders",
        sa.Column("currency", sa.VARCHAR(length=3), nullable=False, server_default="RUB"),
    )
    op.create_check_constraint(
        "ck_orders_delivery_window_valid",
        "orders",
        "delivery_window_end IS NULL OR delivery_window_start IS NULL OR delivery_window_end > delivery_window_start",
    )
    op.create_check_constraint(
        "ck_orders_currency_length",
        "orders",
        "char_length(currency) = 3",
    )

    op.create_table(
        "payment_transactions",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("provider_name", sa.VARCHAR(length=64), nullable=False),
        sa.Column("payment_method", payment_method_enum, nullable=False),
        sa.Column("status", payment_status_enum, nullable=False),
        sa.Column("amount", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.VARCHAR(length=3), nullable=False),
        sa.Column("idempotency_key", sa.VARCHAR(length=128), nullable=False),
        sa.Column("external_payment_id", sa.VARCHAR(length=255), nullable=True),
        sa.Column("redirect_url", sa.VARCHAR(length=512), nullable=True),
        sa.Column("failure_code", sa.VARCHAR(length=64), nullable=True),
        sa.Column("failure_reason", sa.VARCHAR(length=1000), nullable=True),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processed_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "amount >= 0",
            name="ck_payment_transactions_amount_non_negative",
        ),
        sa.CheckConstraint(
            "char_length(currency) = 3",
            name="ck_payment_transactions_currency_length",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_transactions_idempotency_key"),
    )
    op.create_index(
        "ix_payment_transactions_order_id",
        "payment_transactions",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_transactions_status",
        "payment_transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_payment_transactions_provider_name",
        "payment_transactions",
        ["provider_name"],
        unique=False,
    )

    op.create_table(
        "admin_audit_logs",
        sa.Column("admin_user_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.VARCHAR(length=64), nullable=False),
        sa.Column("resource_type", sa.VARCHAR(length=64), nullable=False),
        sa.Column("resource_id", sa.VARCHAR(length=255), nullable=True),
        sa.Column("request_method", sa.VARCHAR(length=10), nullable=False),
        sa.Column("request_path", sa.VARCHAR(length=255), nullable=False),
        sa.Column("status_code", sa.INTEGER(), nullable=False),
        sa.Column("ip_address", sa.VARCHAR(length=64), nullable=True),
        sa.Column("user_agent", sa.VARCHAR(length=512), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["admin_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_audit_logs_admin_user_id",
        "admin_audit_logs",
        ["admin_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_action",
        "admin_audit_logs",
        ["action"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_resource_type",
        "admin_audit_logs",
        ["resource_type"],
        unique=False,
    )
    op.create_index(
        "ix_admin_audit_logs_created_at",
        "admin_audit_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_logs_created_at", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_resource_type", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_action", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_admin_user_id", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")

    op.drop_index("ix_payment_transactions_provider_name", table_name="payment_transactions")
    op.drop_index("ix_payment_transactions_status", table_name="payment_transactions")
    op.drop_index("ix_payment_transactions_order_id", table_name="payment_transactions")
    op.drop_table("payment_transactions")

    op.drop_constraint("ck_orders_currency_length", "orders", type_="check")
    op.drop_constraint("ck_orders_delivery_window_valid", "orders", type_="check")

    op.drop_column("orders", "currency")
    op.drop_column("orders", "payment_status")
    op.drop_column("orders", "payment_method")
    op.drop_column("orders", "delivery_instructions")
    op.drop_column("orders", "delivery_intercom")
    op.drop_column("orders", "delivery_entrance")
    op.drop_column("orders", "delivery_apartment")
    op.drop_column("orders", "delivery_floor")
    op.drop_column("orders", "delivery_country")
    op.drop_column("orders", "delivery_postal_code")
    op.drop_column("orders", "delivery_region")
    op.drop_column("orders", "delivery_city")
    op.drop_column("orders", "delivery_address_line2")
    op.drop_column("orders", "delivery_address_line1")
    op.drop_column("orders", "delivery_window_end")
    op.drop_column("orders", "delivery_window_start")
    op.drop_column("orders", "delivery_method")
    op.drop_column("orders", "customer_comment")
    op.drop_column("orders", "customer_phone")
    op.drop_column("orders", "customer_name")
    op.drop_column("orders", "customer_email")

    postgresql.ENUM(name="paymentstatusenum").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="paymentmethodenum").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="deliverymethodenum").drop(op.get_bind(), checkfirst=True)
