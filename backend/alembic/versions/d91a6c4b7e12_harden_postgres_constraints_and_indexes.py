"""harden postgres constraints and indexes

Revision ID: d91a6c4b7e12
Revises: c4d3b2a190fe
Create Date: 2026-04-23 15:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d91a6c4b7e12"
down_revision: Union[str, Sequence[str], None] = "c4d3b2a190fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE refresh_token
        SET revoked = false
        WHERE revoked IS NULL
        """
    )

    op.create_check_constraint(
        "ck_orders_total_amount_non_negative",
        "orders",
        "total_amount >= 0",
    )
    op.create_check_constraint(
        "ck_order_items_unit_price_non_negative",
        "order_items",
        "unit_price >= 0",
    )
    op.create_check_constraint(
        "ck_order_items_line_total_non_negative",
        "order_items",
        "line_total >= 0",
    )
    op.create_check_constraint(
        "ck_refresh_token_expires_after_create",
        "refresh_token",
        "expires_at > created_at",
    )

    op.alter_column(
        "refresh_token",
        "revoked",
        existing_type=sa.BOOLEAN(),
        server_default=sa.text("false"),
        existing_nullable=False,
    )

    op.drop_constraint("refresh_token_user_id_fkey", "refresh_token", type_="foreignkey")
    op.create_foreign_key(
        "refresh_token_user_id_fkey",
        "refresh_token",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index("ix_refresh_token_user_id", "refresh_token", ["user_id"], unique=False)
    op.create_index("ix_refresh_token_expires_at", "refresh_token", ["expires_at"], unique=False)
    op.create_index("ix_refresh_token_revoked", "refresh_token", ["revoked"], unique=False)
    op.create_index("ix_order_items_product_id", "order_items", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_order_items_product_id", table_name="order_items")
    op.drop_index("ix_refresh_token_revoked", table_name="refresh_token")
    op.drop_index("ix_refresh_token_expires_at", table_name="refresh_token")
    op.drop_index("ix_refresh_token_user_id", table_name="refresh_token")

    op.drop_constraint("refresh_token_user_id_fkey", "refresh_token", type_="foreignkey")
    op.create_foreign_key(
        "refresh_token_user_id_fkey",
        "refresh_token",
        "users",
        ["user_id"],
        ["id"],
    )

    op.alter_column(
        "refresh_token",
        "revoked",
        existing_type=sa.BOOLEAN(),
        server_default=None,
        existing_nullable=False,
    )

    op.drop_constraint(
        "ck_refresh_token_expires_after_create",
        "refresh_token",
        type_="check",
    )
    op.drop_constraint(
        "ck_order_items_line_total_non_negative",
        "order_items",
        type_="check",
    )
    op.drop_constraint(
        "ck_order_items_unit_price_non_negative",
        "order_items",
        type_="check",
    )
    op.drop_constraint(
        "ck_orders_total_amount_non_negative",
        "orders",
        type_="check",
    )
