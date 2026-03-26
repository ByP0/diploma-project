# app/repositories/category_repository.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.category import Category

class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, limit: int = 20, offset: int = 0) -> list[Category]:
        result = await self.session.execute(select(Category).limit(limit).offset(offset))
        return result.scalars().all()

    async def get_by_id(self, category_id: int) -> Category | None:
        return await self.session.get(Category, category_id)

    async def get_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def create(self, category: Category) -> Category:
        self.session.add(category)
        await self.session.flush()
        return category

    async def update(self, category: Category) -> Category:
        await self.session.flush()
        return category

    async def delete(self, category: Category) -> None:
        await self.session.delete(category)
        await self.session.flush()
