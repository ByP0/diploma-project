from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import INTEGER, TIMESTAMP, UUID as PG_UUID, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseWithUUId


class CartItem(BaseWithUUId):
    __tablename__ = "cart_items"
    __allow_nullable__ = {"user_id", "guest_cart_id"}
    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND guest_cart_id IS NULL) OR (user_id IS NULL AND guest_cart_id IS NOT NULL)",
            name="ck_cart_items_owner",
        ),
        CheckConstraint("quantity > 0", name="ck_cart_items_quantity_positive"),
        Index(
            "uq_cart_items_user_product",
            "user_id",
            "product_id",
            unique=True,
            postgresql_where=text("guest_cart_id IS NULL"),
        ),
        Index(
            "uq_cart_items_guest_product",
            "guest_cart_id",
            "product_id",
            unique=True,
            postgresql_where=text("user_id IS NULL"),
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    guest_cart_id: Mapped[str | None] = mapped_column(VARCHAR(64), index=True, nullable=True)
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    quantity: Mapped[int] = mapped_column(INTEGER)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True))

    product = relationship("Product", lazy="joined")
