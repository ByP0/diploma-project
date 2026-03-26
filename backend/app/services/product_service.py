# app/services/product_service.py
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from decimal import Decimal
from typing import Optional

class ProductService:
    def __init__(self, session):
        self.repo = ProductRepository(session)

    async def create(self, name: str, description: str, price: Decimal, category_id: int, stock: int) -> Product:
        product = Product(name=name, description=description, price=price, category_id=category_id, stock=stock)
        created = await self.repo.create(product)
        await self.repo.session.commit()
        await self.repo.session.refresh(created)
        return created

    async def get_list(
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
        return await self.repo.list(search, min_price, max_price, category_id, in_stock, sort_by, limit, offset)

    async def get_by_id(self, product_id) -> Product | None:
        return await self.repo.get_by_id(product_id)

    async def update(self, product: Product) -> Product:
        updated = await self.repo.update(product)
        await self.repo.session.commit()
        return updated

    async def delete(self, product: Product) -> None:
        await self.repo.delete(product)
        await self.repo.session.commit()
