from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, slug: str) -> Category:
        await self.__ensure_slug_unique(slug)

        category = Category(
            name=name,
            slug=slug,
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
            category.slug = slug

        if name:
            category.name = name

        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete(self, category_id: int) -> bool:

        category = await self.get_by_id(category_id)
        if not category:
            return False

        await self.session.delete(category)
        await self.session.commit()
        return True

    async def __ensure_slug_unique(self, slug: str) -> None:
        result = await self.session.execute(
            select(Category).where(Category.slug == slug)
        )
        if result.scalar_one_or_none():
            raise ValueError("Slug already exists")
