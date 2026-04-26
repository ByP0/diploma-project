from __future__ import annotations

from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import INTEGER, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class ProductReview(BaseWithUUId):
    __tablename__ = "product_reviews"
    __allow_nullable__ = {"user_id", "author_name", "moderation_reason"}
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_product_reviews_rating_range"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_product_reviews_status",
        ),
        Index("ix_product_reviews_product_id", "product_id"),
        Index("ix_product_reviews_user_id", "user_id"),
        Index("ix_product_reviews_status", "status"),
        Index("ix_product_reviews_rating", "rating"),
    )

    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
    )
    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    rating: Mapped[int] = mapped_column(INTEGER)
    author_name: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    body: Mapped[str] = mapped_column(VARCHAR(3000))
    status: Mapped[str] = mapped_column(VARCHAR(32), default="pending", server_default="pending")
    moderation_reason: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)

    product = relationship("Product", lazy="joined")
    user = relationship("User", lazy="joined")
