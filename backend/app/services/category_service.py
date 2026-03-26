# app/services/category_service.py
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository

class CategoryService:
    def __init__(self, session):
        self.repo = CategoryRepository(session)

    async def create(self, name: str, slug: str) -> Category:
        existing = await self.repo.get_by_slug(slug)
        if existing:
            raise ValueError("Slug already exists")
        category = Category(name=name, slug=slug)
        created = await self.repo.create(category)
        await self.repo.session.commit()
        await self.repo.session.refresh(created)
        return created

    async def get_list(self, limit: int = 20, offset: int = 0) -> list[Category]:
        return await self.repo.list(limit=limit, offset=offset)

    async def get_by_id(self, category_id: int) -> Category | None:
        return await self.repo.get_by_id(category_id)

    async def update(self, category_id: int, name: str | None, slug: str | None) -> Category | None:
        category = await self.repo.get_by_id(category_id)
        if not category:
            return None
        if slug and slug != category.slug:
            existing = await self.repo.get_by_slug(slug)
            if existing:
                raise ValueError("Slug already exists")
            category.slug = slug
        if name:
            category.name = name
        updated = await self.repo.update(category)
        await self.repo.session.commit()
        await self.repo.session.refresh(updated)
        return updated

    async def delete(self, category_id: int) -> bool:
        category = await self.repo.get_by_id(category_id)
        if not category:
            return False
        await self.repo.delete(category)
        await self.repo.session.commit()
        return True
