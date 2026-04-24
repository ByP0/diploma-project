from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cart_item import CartItem
from app.models.product import Product
from app.schemas.cart import CartItemRead, CartProductSummary, CartRead


class CartService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_cart(self, user_id: UUID) -> CartRead:
        result = await self.session.execute(
            select(CartItem).where(CartItem.user_id == user_id).order_by(CartItem.created_at)
        )
        cart_items = result.scalars().all()
        return self._serialize_cart(cart_items)

    async def add_item(self, user_id: UUID, product_id: UUID, quantity: int) -> CartRead:
        product = await self.session.get(Product, product_id)
        if not product:
            raise ValueError("Товар не найден.")

        if not product.is_active:
            raise ValueError("Товар недоступен для заказа.")

        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )
        cart_item = result.scalar_one_or_none()
        new_quantity = quantity

        if cart_item:
            new_quantity += cart_item.quantity
        else:
            cart_item = CartItem(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity,
            )
            self.session.add(cart_item)

        if new_quantity > product.stock:
            raise ValueError("Запрошенное количество превышает остаток на складе.")

        if cart_item:
            cart_item.quantity = new_quantity

        await self.session.commit()
        return await self.get_cart(user_id)

    async def update_item(self, user_id: UUID, product_id: UUID, quantity: int) -> CartRead:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            raise ValueError("Позиция корзины не найдена.")

        product = await self.session.get(Product, product_id)
        if not product:
            raise ValueError("Товар не найден.")

        if quantity > product.stock:
            raise ValueError("Запрошенное количество превышает остаток на складе.")

        cart_item.quantity = quantity
        await self.session.commit()
        return await self.get_cart(user_id)

    async def remove_item(self, user_id: UUID, product_id: UUID) -> bool:
        result = await self.session.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id,
            )
        )
        cart_item = result.scalar_one_or_none()
        if not cart_item:
            return False

        await self.session.delete(cart_item)
        await self.session.commit()
        return True

    async def clear(self, user_id: UUID) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.user_id == user_id))
        await self.session.commit()

    def _serialize_cart(self, cart_items: list[CartItem]) -> CartRead:
        items: list[CartItemRead] = []
        total_items = 0
        total_amount = Decimal("0.00")

        for cart_item in cart_items:
            product: Product = cart_item.product
            subtotal = (product.price * cart_item.quantity).quantize(Decimal("0.01"))

            items.append(
                CartItemRead(
                    id=cart_item.id,
                    product_id=cart_item.product_id,
                    quantity=cart_item.quantity,
                    subtotal=subtotal,
                    created_at=cart_item.created_at,
                    updated_at=cart_item.updated_at,
                    product=CartProductSummary(
                    id=product.id,
                    sku=product.sku,
                    name=product.name,
                    brand=product.brand,
                    price=product.price,
                    unit=product.unit.value,
                    stock=product.stock,
                    photo_ids=product.photo_ids,
                ),
            )
            )
            total_items += cart_item.quantity
            total_amount += subtotal

        return CartRead(
            items=items,
            total_items=total_items,
            total_amount=total_amount.quantize(Decimal("0.01")),
        )
