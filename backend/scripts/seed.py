from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.security import password_service
from app.db.postgres import db_postgres
from app.models.category import Category
from app.models.product import Product, ProductUnitEnum
from app.models.user import User, UserRoleEnum


async def seed_admin() -> None:
    async with db_postgres.session_factory() as session:
        admin_email = "admin@example.com"
        existing_admin = await session.scalar(select(User).where(User.email == admin_email))
        if existing_admin is None:
            session.add(
                User(
                    email=admin_email,
                    name="Admin",
                    hashed_password=password_service.hash_password("admin12345"),
                    role=UserRoleEnum.ADMIN,
                    is_active=True,
                )
            )

        categories = [
            Category(id=1, name="Fruits", slug="fruits"),
            Category(id=2, name="Vegetables", slug="vegetables"),
            Category(id=3, name="Dairy", slug="dairy"),
        ]
        for category in categories:
            existing_category = await session.get(Category, category.id)
            if existing_category is None:
                session.add(category)

        existing_product = await session.scalar(select(Product).where(Product.sku == "APPLE-001"))
        if existing_product is None:
            session.add(
                Product(
                    sku="APPLE-001",
                    name="Apple",
                    brand="Seed Store",
                    description="Seed product for local development.",
                    price=Decimal("99.90"),
                    unit=ProductUnitEnum.KILOGRAM,
                    is_active=True,
                    photo_ids=[],
                    category_id=1,
                    stock=100,
                    reserved_stock=0,
                )
            )

        await session.commit()


def main() -> None:
    asyncio.run(seed_admin())


if __name__ == "__main__":
    main()
