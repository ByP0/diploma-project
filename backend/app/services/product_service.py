from decimal import Decimal
from typing import Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.product import Product, ProductUnitEnum


class ProductService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        sku: str,
        name: str,
        brand: str | None,
        description: str,
        price: Decimal,
        unit: ProductUnitEnum,
        is_active: bool,
        photo_ids: list[str],
        category_id: int,
        stock: int,
    ) -> Product:
        await self.__ensure_sku_unique(sku)

        if not await self.__get_category_by_id(category_id):
            raise ValueError("Категория не найдена.")

        product = Product(
            sku=sku.strip().upper(),
            name=name.strip(),
            brand=brand.strip() if brand else None,
            description=description.strip(),
            price=price,
            unit=unit,
            is_active=is_active,
            photo_ids=photo_ids,
            category_id=category_id,
            stock=stock,
        )

        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get_list(
        self,
        limit: int = 20,
        offset: int = 0,
        category_id: int | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        search: str | None = None,
        active_only: bool = True,
    ) -> Sequence[Product]:
        statement = select(Product)

        if active_only:
            statement = statement.where(Product.is_active.is_(True))

        if category_id is not None:
            statement = statement.where(Product.category_id == category_id)

        if min_price is not None:
            statement = statement.where(Product.price >= min_price)

        if max_price is not None:
            statement = statement.where(Product.price <= max_price)

        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Product.name.ilike(pattern),
                    Product.brand.ilike(pattern),
                    Product.description.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            )

        result = await self.session.execute(
            statement.order_by(Product.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def get_by_id(self, product_id: UUID) -> Product | None:
        return await self.session.get(Product, product_id)

    async def update(
        self,
        product_id: UUID,
        sku: str | None = None,
        name: str | None = None,
        brand: str | None = None,
        description: str | None = None,
        price: Decimal | None = None,
        unit: ProductUnitEnum | None = None,
        is_active: bool | None = None,
        photo_ids: list[str] | None = None,
        category_id: int | None = None,
        stock: int | None = None,
    ) -> Product | None:
        product = await self.get_by_id(product_id)
        if not product:
            return None

        if sku and sku.strip().upper() != product.sku:
            normalized_sku = sku.strip().upper()
            await self.__ensure_sku_unique(normalized_sku, exclude_product_id=product.id)
            product.sku = normalized_sku

        if name:
            product.name = name.strip()

        if brand is not None:
            product.brand = brand.strip() or None

        if description is not None:
            product.description = description.strip()

        if price is not None:
            product.price = price

        if unit is not None:
            product.unit = unit

        if is_active is not None:
            product.is_active = is_active

        if photo_ids is not None:
            product.photo_ids = photo_ids

        if category_id is not None:
            if not await self.__get_category_by_id(category_id):
                raise ValueError("Категория не найдена.")
            product.category_id = category_id

        if stock is not None:
            product.stock = stock

        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: UUID) -> bool:
        product = await self.get_by_id(product_id)
        if not product:
            return False

        await self.session.delete(product)
        await self.session.commit()
        return True

    async def detach_photo_id(self, photo_id: str) -> int:
        result = await self.session.execute(
            select(Product).where(Product.photo_ids.any(photo_id))
        )
        products = result.scalars().all()

        for product in products:
            product.photo_ids = [
                current_photo_id
                for current_photo_id in product.photo_ids
                if current_photo_id != photo_id
            ]

        if products:
            await self.session.commit()

        return len(products)

    async def __ensure_sku_unique(
        self,
        sku: str,
        exclude_product_id: UUID | None = None,
    ) -> None:
        statement = select(Product).where(Product.sku == sku)

        if exclude_product_id is not None:
            statement = statement.where(Product.id != exclude_product_id)

        result = await self.session.execute(statement)

        if result.scalar_one_or_none():
            raise ValueError("Товар с таким артикулом уже существует.")

    async def __get_category_by_id(self, category_id: int) -> Category | None:
        return await self.session.get(Category, category_id)
