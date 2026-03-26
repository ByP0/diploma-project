# app/models/product.py

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import TEXT, NUMERIC, SMALLINT, INTEGER
from decimal import Decimal

from app.models.base import BaseWithUUID

class Product(BaseWithUUID):
    __tablename__ = 'products'

    name: Mapped[str] = mapped_column(TEXT)
    description: Mapped[str] = mapped_column(TEXT)
    price: Mapped[Decimal] = mapped_column(NUMERIC(10, 2))
    category_id: Mapped[int] = mapped_column(SMALLINT, ForeignKey('categories.id'))
    stock: Mapped[int] = mapped_column(INTEGER)
