from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Sequence
from decimal import Decimal

from app.models.product import Product
from app.models.category import Category


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        description: str,
        price: Decimal,     
        category_id: int,
        stock: int,
    ) -> Product:
        await self.__ensure_name_unique(name)

        if not await self.__get_category_by_id(category_id):
            raise ValueError("Category not found")

        product = Product(
            name=name,
            description=description,
            price=price,
            category_id=price,
            stock=stock
        )

        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product
    
    async def get_list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Product]:
        
        result = await self.session.execute(
            select(Product)
            .limit(limit)
            .offset(offset)
        )

        return result.scalars().all()
    
    async def get_list_by_category(
        self,
    ) -> Sequence[Product]: pass

    async def get_by_name(
        self,
    ) -> Sequence[Product]: pass

    async def get_by_id(
        self
    ) -> Product | None: pass

    async def __ensure_name_unique(self, name: str) -> None:
        result = await self.session.execute(
            select(Product).where(Product.name == name)
        )
        if result.scalar_one_or_none():
            raise ValueError("Slug already exists")

    async def __get_category_by_id(self, category_id: int) -> Category | None:
        return await self.session.get(Category, category_id)
