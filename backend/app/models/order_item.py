from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import INTEGER, NUMERIC, TEXT, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseWithUUId


class OrderItem(BaseWithUUId):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("returned_quantity >= 0", name="ck_order_items_returned_quantity_non_negative"),
        CheckConstraint("returned_quantity <= quantity", name="ck_order_items_returned_quantity_lte_quantity"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        CheckConstraint("line_total >= 0", name="ck_order_items_line_total_non_negative"),
    )

    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_name: Mapped[str] = mapped_column(TEXT)
    unit_price: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    quantity: Mapped[int] = mapped_column(INTEGER)
    returned_quantity: Mapped[int] = mapped_column(INTEGER, default=0, server_default="0")
    line_total: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
