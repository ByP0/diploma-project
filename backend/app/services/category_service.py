from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.product import Product


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, category_id: int, name: str, slug: str) -> Category:
        if await self.get_by_id(category_id):
            raise ValueError("Категория с таким идентификатором уже существует.")

        await self.__ensure_slug_unique(slug)

        category = Category(
            id=category_id,
            name=name.strip(),
            slug=slug.strip().lower(),
        )

        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def get_list(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[Category]:

        result = await self.session.execute(
            select(Category)
            .order_by(Category.name.asc())
            .offset(offset)
            .limit(limit)
        )

        return result.scalars().all()

    async def get_by_id(self, category_id: int) -> Category | None:
        return await self.session.get(Category, category_id)

    async def update(
        self,
        category_id: int,
        name: str | None = None,
        slug: str | None = None,
    ) -> Category | None:

        category = await self.get_by_id(category_id)
        if not category:
            return None

        if slug and slug != category.slug:
            await self.__ensure_slug_unique(slug)
            category.slug = slug.strip().lower()

        if name:
            category.name = name.strip()

        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: int) -> bool:

        category = await self.get_by_id(category_id)
        if not category:
            return False

        linked_product = await self.session.execute(
            select(Product.id).where(Product.category_id == category_id).limit(1)
        )
        if linked_product.scalar_one_or_none() is not None:
            raise ValueError(
                "Нельзя удалить категорию, пока в ней существуют товары каталога."
            )

        await self.session.delete(category)
        await self.session.commit()
        return True

    async def __ensure_slug_unique(self, slug: str) -> None:
        result = await self.session.execute(
            select(Category).where(Category.slug == slug)
        )
        if result.scalar_one_or_none():
            raise ValueError("Категория с таким slug уже существует.")
