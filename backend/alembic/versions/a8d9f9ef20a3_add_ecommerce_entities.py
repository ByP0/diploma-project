"""add ecommerce entities

Revision ID: a8d9f9ef20a3
Revises: 379581e7e4e2
Create Date: 2026-04-23 13:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a8d9f9ef20a3"
down_revision: Union[str, Sequence[str], None] = "379581e7e4e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    order_status_enum = postgresql.ENUM(
        "PENDING",
        "PAID",
        "DELIVERED",
        name="orderstatusenum",
        create_type=False,
    )
    order_status_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "products",
        sa.Column(
            "photo_ids",
            postgresql.ARRAY(sa.TEXT()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
    )
    op.create_check_constraint(
        "ck_products_stock_non_negative",
        "products",
        "stock >= 0",
    )

    op.create_table(
        "cart_items",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.INTEGER(), nullable=False),
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
            "quantity > 0",
            name="ck_cart_items_quantity_positive",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_cart_items_user_product"),
    )
    op.create_index(op.f("ix_cart_items_user_id"), "cart_items", ["user_id"], unique=False)
    op.create_index(op.f("ix_cart_items_product_id"), "cart_items", ["product_id"], unique=False)

    op.create_table(
        "orders",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", order_status_enum, nullable=False),
        sa.Column("total_amount", sa.NUMERIC(precision=10, scale=2), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)

    op.create_table(
        "order_items",
        sa.Column("order_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=True),
        sa.Column("product_name", sa.TEXT(), nullable=False),
        sa.Column("unit_price", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column("quantity", sa.INTEGER(), nullable=False),
        sa.Column("line_total", sa.NUMERIC(precision=10, scale=2), nullable=False),
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
        sa.CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_order_items_order_id"), table_name="order_items")
    op.drop_table("order_items")

    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_cart_items_product_id"), table_name="cart_items")
    op.drop_index(op.f("ix_cart_items_user_id"), table_name="cart_items")
    op.drop_table("cart_items")

    op.drop_constraint("ck_products_stock_non_negative", "products", type_="check")
    op.drop_column("products", "photo_ids")

    postgresql.ENUM(name="orderstatusenum").drop(op.get_bind(), checkfirst=True)
