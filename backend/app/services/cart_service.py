from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.domain_events import CartCreated, CartExpired, CartItemAdded, CartItemRemoved, CartUpdated
from app.events.publishers.event_publisher import EventPublisher
from app.models.cart_item import CartItem
from app.models.product import Product
from app.schemas.cart import CartItemRead, CartProductSummary, CartRead, GuestCartSessionRead
from app.services.inventory_service import InventoryService


class CartService:
    ttl = timedelta(days=10)

    def __init__(self, session: AsyncSession):
        self.session = session
        self.event_publisher = EventPublisher(session)
        self.inventory_service = InventoryService(session)

    async def create_guest_cart_session(self) -> GuestCartSessionRead:
        now = datetime.now(timezone.utc)
        guest_session = GuestCartSessionRead(
            guest_cart_id=uuid4().hex,
            expires_at=now + self.ttl,
        )
        cart_id, owner_type, owner_id = self._build_cart_identity(guest_cart_id=guest_session.guest_cart_id)
        await self.event_publisher.publish_domain(
            CartCreated(
                cart_id=cart_id,
                owner_type=owner_type,
                owner_id=owner_id,
            )
        )
        await self.session.commit()
        return guest_session

    async def get_cart(
        self,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
    ) -> CartRead:
        await self._cleanup_expired(user_id=user_id, guest_cart_id=guest_cart_id)
        items = await self._get_cart_items(user_id=user_id, guest_cart_id=guest_cart_id)
        return self._serialize_cart(items, guest_cart_id=guest_cart_id)

    async def add_item(
        self,
        *,
        product_id: UUID,
        quantity: int,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
    ) -> CartRead:
        self._validate_owner(user_id=user_id, guest_cart_id=guest_cart_id)
        await self._cleanup_expired(user_id=user_id, guest_cart_id=guest_cart_id)
        existing_items = await self._get_cart_items(user_id=user_id, guest_cart_id=guest_cart_id)

        product = await self.session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found.")
        if not product.is_active:
            raise ValueError("Product is not available.")

        cart_item = await self._get_cart_item(
            user_id=user_id,
            guest_cart_id=guest_cart_id,
            product_id=product_id,
        )
        new_quantity = quantity + (cart_item.quantity if cart_item else 0)
        if new_quantity > self.inventory_service.get_available_stock(product):
            raise ValueError("Requested quantity exceeds available stock.")

        expires_at = datetime.now(timezone.utc) + self.ttl
        if cart_item:
            cart_item.quantity = new_quantity
            cart_item.expires_at = expires_at
        else:
            cart_item = CartItem(
                user_id=user_id,
                guest_cart_id=guest_cart_id,
                product_id=product_id,
                quantity=quantity,
                expires_at=expires_at,
            )
            self.session.add(cart_item)

        cart_id, owner_type, owner_id = self._build_cart_identity(user_id=user_id, guest_cart_id=guest_cart_id)
        if not existing_items:
            await self.event_publisher.publish_domain(
                CartCreated(
                    cart_id=cart_id,
                    owner_type=owner_type,
                    owner_id=owner_id,
                )
            )
        await self.event_publisher.publish_domain(
            CartItemAdded(
                cart_id=cart_id,
                owner_type=owner_type,
                owner_id=owner_id,
                product_id=str(product_id),
                quantity=quantity,
            )
        )
        await self.session.commit()
        return await self.get_cart(user_id=user_id, guest_cart_id=guest_cart_id)

    async def update_item(
        self,
        *,
        product_id: UUID,
        quantity: int,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
    ) -> CartRead:
        self._validate_owner(user_id=user_id, guest_cart_id=guest_cart_id)
        cart_item = await self._get_cart_item(
            user_id=user_id,
            guest_cart_id=guest_cart_id,
            product_id=product_id,
        )
        if not cart_item:
            raise ValueError("Cart item not found.")

        product = await self.session.get(Product, product_id)
        if not product:
            raise ValueError("Product not found.")
        if quantity > self.inventory_service.get_available_stock(product):
            raise ValueError("Requested quantity exceeds available stock.")

        cart_item.quantity = quantity
        cart_item.expires_at = datetime.now(timezone.utc) + self.ttl
        cart_id, owner_type, owner_id = self._build_cart_identity(user_id=user_id, guest_cart_id=guest_cart_id)
        await self.event_publisher.publish_domain(
            CartUpdated(
                cart_id=cart_id,
                owner_type=owner_type,
                owner_id=owner_id,
                product_id=str(product_id),
                quantity=quantity,
            )
        )
        await self.session.commit()
        return await self.get_cart(user_id=user_id, guest_cart_id=guest_cart_id)

    async def remove_item(
        self,
        *,
        product_id: UUID,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
    ) -> bool:
        cart_item = await self._get_cart_item(
            user_id=user_id,
            guest_cart_id=guest_cart_id,
            product_id=product_id,
        )
        if not cart_item:
            return False

        cart_id, owner_type, owner_id = self._build_cart_identity(user_id=user_id, guest_cart_id=guest_cart_id)
        await self.session.delete(cart_item)
        await self.event_publisher.publish_domain(
            CartItemRemoved(
                cart_id=cart_id,
                owner_type=owner_type,
                owner_id=owner_id,
                product_id=str(product_id),
            )
        )
        await self.session.commit()
        return True

    async def clear(
        self,
        *,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
    ) -> None:
        self._validate_owner(user_id=user_id, guest_cart_id=guest_cart_id)
        await self.session.execute(
            delete(CartItem).where(*self._cart_filters(user_id=user_id, guest_cart_id=guest_cart_id))
        )
        await self.session.commit()

    async def _cleanup_expired(
        self,
        *,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
    ) -> None:
        self._validate_owner(user_id=user_id, guest_cart_id=guest_cart_id)
        expired_items = await self._get_expired_cart_items(user_id=user_id, guest_cart_id=guest_cart_id)
        if not expired_items:
            return

        await self.session.execute(
            delete(CartItem).where(
                *self._cart_filters(user_id=user_id, guest_cart_id=guest_cart_id),
                CartItem.expires_at <= datetime.now(timezone.utc),
            )
        )
        cart_id, owner_type, owner_id = self._build_cart_identity(user_id=user_id, guest_cart_id=guest_cart_id)
        await self.event_publisher.publish_domain(
            CartExpired(
                cart_id=cart_id,
                owner_type=owner_type,
                owner_id=owner_id,
                expired_items=len(expired_items),
            )
        )
        await self.session.commit()

    async def _get_cart_items(
        self,
        *,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
    ) -> list[CartItem]:
        result = await self.session.execute(
            select(CartItem)
            .where(*self._cart_filters(user_id=user_id, guest_cart_id=guest_cart_id))
            .order_by(CartItem.created_at)
        )
        return list(result.scalars().all())

    async def _get_cart_item(
        self,
        *,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
        product_id: UUID,
    ) -> CartItem | None:
        result = await self.session.execute(
            select(CartItem).where(
                *self._cart_filters(user_id=user_id, guest_cart_id=guest_cart_id),
                CartItem.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_expired_cart_items(
        self,
        *,
        user_id: UUID | None = None,
        guest_cart_id: str | None = None,
    ) -> list[CartItem]:
        result = await self.session.execute(
            select(CartItem).where(
                *self._cart_filters(user_id=user_id, guest_cart_id=guest_cart_id),
                CartItem.expires_at <= datetime.now(timezone.utc),
            )
        )
        return list(result.scalars().all())

    def _serialize_cart(
        self,
        cart_items: list[CartItem],
        *,
        guest_cart_id: str | None = None,
    ) -> CartRead:
        items: list[CartItemRead] = []
        total_items = 0
        total_amount = Decimal("0.00")
        expires_at = max((item.expires_at for item in cart_items), default=None)

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
                    expires_at=cart_item.expires_at,
                    product=CartProductSummary(
                        id=product.id,
                        sku=product.sku,
                        name=product.name,
                        brand=product.brand,
                        price=product.price,
                        unit=product.unit.value,
                        stock=product.stock,
                        reserved_stock=product.reserved_stock,
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
            guest_cart_id=guest_cart_id,
            expires_at=expires_at,
        )

    @staticmethod
    def _validate_owner(*, user_id: UUID | None, guest_cart_id: str | None) -> None:
        if (user_id is None) == (guest_cart_id is None):
            raise ValueError("Exactly one cart owner must be provided.")

    @staticmethod
    def _cart_filters(*, user_id: UUID | None, guest_cart_id: str | None):
        if user_id is not None:
            return (CartItem.user_id == user_id, CartItem.guest_cart_id.is_(None))
        return (CartItem.user_id.is_(None), CartItem.guest_cart_id == guest_cart_id)

    @staticmethod
    def _build_cart_identity(*, user_id: UUID | None = None, guest_cart_id: str | None = None) -> tuple[str, str, str]:
        if user_id is not None:
            owner_id = str(user_id)
            return owner_id, "user", owner_id
        if guest_cart_id is None:
            raise ValueError("Guest cart id is required for guest cart events.")
        return guest_cart_id, "guest", guest_cart_id
