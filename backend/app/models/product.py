import enum

from sqlalchemy import BOOLEAN, CheckConstraint, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY, INTEGER, NUMERIC, SMALLINT, TEXT, VARCHAR
from decimal import Decimal

from app.models.base import BaseWithUUId


class ProductUnitEnum(str, enum.Enum):
    PIECE = "шт"
    KILOGRAM = "кг"
    GRAM = "г"
    LITER = "л"
    MILLILITER = "мл"
    PACK = "уп"


class Product(BaseWithUUId):
    __tablename__ = 'products'
    __table_args__ = (
        UniqueConstraint("sku", name="uq_products_sku"),
        CheckConstraint("stock >= 0", name="ck_products_stock_non_negative"),
        CheckConstraint("price >= 0", name="ck_products_price_non_negative"),
    )

    sku: Mapped[str] = mapped_column(VARCHAR(64))
    name: Mapped[str] = mapped_column(VARCHAR(120))
    brand: Mapped[str | None] = mapped_column(VARCHAR(120), nullable=True)
    description: Mapped[str] = mapped_column(TEXT)
    price: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    unit: Mapped[ProductUnitEnum] = mapped_column(default=ProductUnitEnum.PIECE)
    is_active: Mapped[bool] = mapped_column(BOOLEAN, default=True, server_default=text("true"))
    photo_ids: Mapped[list[str]] = mapped_column(
        ARRAY(TEXT),
        default=list,
        server_default=text("'{}'::text[]"),
    )
    category_id: Mapped[int] = mapped_column(SMALLINT, ForeignKey('categories.id'), index=True)
    stock: Mapped[int] = mapped_column(INTEGER)
