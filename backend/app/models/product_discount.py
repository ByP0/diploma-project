from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import BOOLEAN, CheckConstraint, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INTEGER, NUMERIC, SMALLINT, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class ProductDiscount(BaseWithUUId):
    __tablename__ = "product_discounts"
    __allow_nullable__ = {
        "code",
        "description",
        "product_id",
        "category_id",
        "starts_at",
        "ends_at",
        "usage_limit",
    }
    __table_args__ = (
        CheckConstraint("discount_type IN ('percent', 'fixed')", name="ck_product_discounts_type"),
        CheckConstraint("value >= 0", name="ck_product_discounts_value_non_negative"),
        CheckConstraint(
            "discount_type != 'percent' OR value <= 100",
            name="ck_product_discounts_percent_lte_100",
        ),
        CheckConstraint("usage_limit IS NULL OR usage_limit >= 0", name="ck_product_discounts_usage_limit_non_negative"),
        CheckConstraint("used_count >= 0", name="ck_product_discounts_used_count_non_negative"),
        CheckConstraint(
            "ends_at IS NULL OR starts_at IS NULL OR ends_at > starts_at",
            name="ck_product_discounts_period_valid",
        ),
        UniqueConstraint("code", name="uq_product_discounts_code"),
        Index("ix_product_discounts_product_id", "product_id"),
        Index("ix_product_discounts_category_id", "category_id"),
        Index("ix_product_discounts_is_active", "is_active"),
        Index("ix_product_discounts_starts_at", "starts_at"),
        Index("ix_product_discounts_ends_at", "ends_at"),
    )

    name: Mapped[str] = mapped_column(VARCHAR(120))
    code: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    description: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    discount_type: Mapped[str] = mapped_column(VARCHAR(16), default="percent", server_default="percent")
    value: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, server_default=text("true"))
    product_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        SMALLINT,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
    )
    starts_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(INTEGER, nullable=True)
    used_count: Mapped[int] = mapped_column(INTEGER, default=0, server_default="0")

    product = relationship("Product", lazy="joined")
    category = relationship("Category", lazy="joined")
