# app/repositories/product_repository.py
from uuid import UUID
from decimal import Decimal
from typing import Optional
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.product import Product

class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: UUID) -> Product | None:
        return await self.session.get(Product, product_id)

    async def list(
        self,
        search: Optional[str] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        category_id: Optional[int] = None,
        in_stock: Optional[bool] = None,
        sort_by: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Product]:
        stmt = select(Product)
        conditions = []
        if search:
            conditions.append(or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            ))
        if min_price is not None:
            conditions.append(Product.price >= min_price)
        if max_price is not None:
            conditions.append(Product.price <= max_price)
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if in_stock:
            conditions.append(Product.stock > 0)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        if sort_by == "price_asc":
            stmt = stmt.order_by(asc(Product.price))
        elif sort_by == "price_desc":
            stmt = stmt.order_by(desc(Product.price))
        elif sort_by == "new":
            stmt = stmt.order_by(desc(Product.created_at))

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        return product

    async def update(self, product: Product) -> Product:
        await self.session.flush()
        return product

    async def delete(self, product: Product) -> None:
        await self.session.delete(product)
        await self.session.flush()
