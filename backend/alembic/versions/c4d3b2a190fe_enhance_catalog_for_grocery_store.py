"""enhance catalog for grocery store

Revision ID: c4d3b2a190fe
Revises: a8d9f9ef20a3
Create Date: 2026-04-23 13:55:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c4d3b2a190fe"
down_revision: Union[str, Sequence[str], None] = "a8d9f9ef20a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    product_unit_enum = postgresql.ENUM(
        "PIECE",
        "KILOGRAM",
        "GRAM",
        "LITER",
        "MILLILITER",
        "PACK",
        name="productunitenum",
        create_type=False,
    )
    product_unit_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("products", sa.Column("sku", sa.VARCHAR(length=64), nullable=True))
    op.add_column("products", sa.Column("brand", sa.VARCHAR(length=120), nullable=True))
    op.add_column(
        "products",
        sa.Column(
            "unit",
            product_unit_enum,
            nullable=False,
            server_default="PIECE",
        ),
    )
    op.add_column(
        "products",
        sa.Column(
            "is_active",
            sa.BOOLEAN(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.execute(
        """
        UPDATE products
        SET sku = CONCAT('SKU-', UPPER(SUBSTRING(REPLACE(id::text, '-', ''), 1, 12)))
        WHERE sku IS NULL
        """
    )
    op.alter_column("products", "sku", nullable=False)
    op.create_unique_constraint("uq_products_sku", "products", ["sku"])
    op.create_index("ix_products_category_id", "products", ["category_id"], unique=False)
    op.create_index("ix_products_is_active", "products", ["is_active"], unique=False)
    op.create_check_constraint(
        "ck_products_price_non_negative",
        "products",
        "price >= 0",
    )
    op.create_unique_constraint("uq_categories_slug", "categories", ["slug"])
    op.execute("ALTER TYPE orderstatusenum ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade() -> None:
    op.execute("UPDATE orders SET status = 'PENDING' WHERE status = 'CANCELLED'")

    op.drop_constraint("uq_categories_slug", "categories", type_="unique")
    op.drop_constraint("ck_products_price_non_negative", "products", type_="check")
    op.drop_index("ix_products_is_active", table_name="products")
    op.drop_index("ix_products_category_id", table_name="products")
    op.drop_constraint("uq_products_sku", "products", type_="unique")
    op.drop_column("products", "is_active")
    op.drop_column("products", "unit")
    op.drop_column("products", "brand")
    op.drop_column("products", "sku")

    op.execute("ALTER TYPE orderstatusenum RENAME TO orderstatusenum_old")
    restored_enum = postgresql.ENUM(
        "PENDING",
        "PAID",
        "DELIVERED",
        name="orderstatusenum",
    )
    restored_enum.create(op.get_bind(), checkfirst=True)
    op.execute(
        """
        ALTER TABLE orders
        ALTER COLUMN status TYPE orderstatusenum
        USING status::text::orderstatusenum
        """
    )
    postgresql.ENUM(name="orderstatusenum_old").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="productunitenum").drop(op.get_bind(), checkfirst=True)
