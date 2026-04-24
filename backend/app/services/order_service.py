from __future__ import annotations

from decimal import Decimal
import logging
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart_item import CartItem
from app.models.order import Order, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.observability.metrics import metrics_registry
from app.schemas.order import OrderCheckoutCreate
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.services.payment_service import PaymentService


logger = logging.getLogger(__name__)


ORDER_STATUS_TRANSITIONS: dict[OrderStatusEnum, set[OrderStatusEnum]] = {
    OrderStatusEnum.PENDING: {
        OrderStatusEnum.PAID,
        OrderStatusEnum.CONFIRMED,
        OrderStatusEnum.CANCELLED,
    },
    OrderStatusEnum.PAID: {
        OrderStatusEnum.CONFIRMED,
        OrderStatusEnum.CANCELLED,
    },
    OrderStatusEnum.CONFIRMED: {
        OrderStatusEnum.OUT_FOR_DELIVERY,
        OrderStatusEnum.CANCELLED,
    },
    OrderStatusEnum.OUT_FOR_DELIVERY: {
        OrderStatusEnum.DELIVERED,
        OrderStatusEnum.CANCELLED,
    },
    OrderStatusEnum.DELIVERED: set(),
    OrderStatusEnum.CANCELLED: set(),
}


class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.payment_service = PaymentService(session)
        self.notification_service = NotificationService()
        self.alert_service = AlertService()

    async def create_from_cart(self, user: User, checkout_data: OrderCheckoutCreate) -> Order:
        try:
            cart_items = await self._get_cart_items(user.id)
            if not cart_items:
                raise ValueError("Корзина пуста.")

            total_amount = Decimal("0.00")
            order_items: list[OrderItem] = []

            product_ids = [item.product_id for item in cart_items]
            products_result = await self.session.execute(
                select(Product).where(Product.id.in_(product_ids)).with_for_update()
            )
            products_by_id = {product.id: product for product in products_result.scalars().all()}

            for cart_item in cart_items:
                product = products_by_id.get(cart_item.product_id)
                if not product:
                    raise ValueError("Один из товаров в корзине больше не существует.")
                if not product.is_active:
                    raise ValueError(f"Товар «{product.name}» временно недоступен для заказа.")
                if cart_item.quantity > product.stock:
                    raise ValueError(
                        f"Недостаточно товара «{product.name}» на складе. Доступно: {product.stock}."
                    )

                line_total = (product.price * cart_item.quantity).quantize(Decimal("0.01"))
                total_amount += line_total
                product.stock -= cart_item.quantity
                order_items.append(
                    OrderItem(
                        product_id=product.id,
                        product_name=product.name,
                        unit_price=product.price,
                        quantity=cart_item.quantity,
                        line_total=line_total,
                    )
                )

            order = Order(
                user_id=user.id,
                status=OrderStatusEnum.PENDING,
                total_amount=total_amount.quantize(Decimal("0.01")),
                customer_email=user.email,
                customer_name=checkout_data.customer_name,
                customer_phone=checkout_data.customer_phone,
                customer_comment=checkout_data.customer_comment,
                delivery_method=checkout_data.delivery_method,
                delivery_window_start=checkout_data.delivery_window_start,
                delivery_window_end=checkout_data.delivery_window_end,
                delivery_address_line1=checkout_data.delivery_address_line1,
                delivery_address_line2=checkout_data.delivery_address_line2,
                delivery_city=checkout_data.delivery_city,
                delivery_region=checkout_data.delivery_region,
                delivery_postal_code=checkout_data.delivery_postal_code,
                delivery_country=checkout_data.delivery_country,
                delivery_floor=checkout_data.delivery_floor,
                delivery_apartment=checkout_data.delivery_apartment,
                delivery_entrance=checkout_data.delivery_entrance,
                delivery_intercom=checkout_data.delivery_intercom,
                delivery_instructions=checkout_data.delivery_instructions,
                payment_method=checkout_data.payment_method,
                payment_status=PaymentStatusEnum.PENDING,
                currency=checkout_data.currency,
            )
            self.session.add(order)
            await self.session.flush()

            for order_item in order_items:
                order_item.order_id = order.id
                self.session.add(order_item)

            await self.payment_service.create_checkout_payment(order)
            await self.session.execute(delete(CartItem).where(CartItem.user_id == user.id))
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        created_order = await self.get_by_id_for_user(user.id, order.id)
        if not created_order:
            raise ValueError("Не удалось загрузить только что созданный заказ.")

        metrics_registry.increment(
            "shop_orders_created_total",
            payment_method=created_order.payment_method.value,
            delivery_method=created_order.delivery_method.value,
        )
        await self._send_order_created_notifications(created_order)
        return created_order

    async def retry_payment(self, user_id: UUID, order_id: UUID) -> Order | None:
        order = await self.get_by_id_for_user(user_id, order_id)
        if not order:
            return None

        await self.payment_service.retry_payment(order)
        await self.session.commit()

        refreshed_order = await self.get_by_id_for_user(user_id, order_id)
        if refreshed_order:
            await self._send_order_status_notifications(refreshed_order)
        return refreshed_order

    async def get_history(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment_transactions),
            )
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id_for_user(self, user_id: UUID, order_id: UUID) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment_transactions),
            )
        )
        return result.scalar_one_or_none()

    async def update_status(self, order_id: UUID, status: OrderStatusEnum) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.payment_transactions))
        )
        order = result.scalar_one_or_none()
        if not order:
            return None

        if status != order.status:
            allowed_statuses = ORDER_STATUS_TRANSITIONS.get(order.status, set())
            if status not in allowed_statuses:
                raise ValueError(
                    f"Нельзя перевести заказ из статуса '{order.status.value}' "
                    f"в '{status.value}'."
                )

        order.status = status

        if status == OrderStatusEnum.PAID:
            order.payment_status = PaymentStatusEnum.SUCCEEDED

        if status == OrderStatusEnum.DELIVERED:
            await self.payment_service.mark_offline_payment_succeeded(order)

        if status == OrderStatusEnum.CANCELLED:
            if order.payment_status == PaymentStatusEnum.PENDING:
                await self.payment_service.cancel_pending_payment(order)
            elif (
                order.payment_method == PaymentMethodEnum.CARD_ONLINE
                and order.payment_status == PaymentStatusEnum.SUCCEEDED
            ):
                await self.alert_service.notify(
                    kind="manual_refund_required",
                    severity="warning",
                    message="Заказ с успешной онлайн-оплатой был отменён и требует ручной сверки возврата.",
                    context={"order_id": str(order.id)},
                )

        await self.session.commit()

        refreshed_order = await self._get_by_id(order_id)
        if refreshed_order:
            await self._send_order_status_notifications(refreshed_order)
        return refreshed_order

    async def _get_cart_items(self, user_id: UUID) -> list[CartItem]:
        cart_result = await self.session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
        )
        return list(cart_result.scalars().all())

    async def _get_by_id(self, order_id: UUID) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.payment_transactions))
        )
        return result.scalar_one_or_none()

    async def _send_order_created_notifications(self, order: Order) -> None:
        try:
            latest_payment = order.payment_transactions[-1] if order.payment_transactions else None
            await self.notification_service.send_order_created(order, latest_payment)
        except Exception as exc:  # pragma: no cover - defensive notification guard
            logger.exception("Order creation notification failed: %s", exc)
            await self.alert_service.notify(
                kind="order_notification_failed",
                severity="warning",
                message="Не удалось отправить уведомление о новом заказе.",
                context={"order_id": str(order.id)},
            )

    async def _send_order_status_notifications(self, order: Order) -> None:
        try:
            await self.notification_service.send_order_status_updated(order)
        except Exception as exc:  # pragma: no cover - defensive notification guard
            logger.exception("Order status notification failed: %s", exc)
            await self.alert_service.notify(
                kind="order_status_notification_failed",
                severity="warning",
                message="Не удалось отправить уведомление о смене статуса заказа.",
                context={"order_id": str(order.id)},
            )
