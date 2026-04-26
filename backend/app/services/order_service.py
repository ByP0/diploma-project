from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.events.domain_events import (
    OrderCancelled,
    OrderConfirmed,
    OrderCreated,
    OrderDelivered,
    OrderPacked,
    OrderPaid,
    OrderPaymentFailed,
    OrderProcessingStarted,
    OrderRefunded,
    OrderShipped,
)
from app.events.publishers.event_publisher import EventPublisher
from app.models.cart_item import CartItem
from app.models.order import Order, OrderStatusEnum, PaymentStatusEnum
from app.models.order_item import OrderItem
from app.models.order_status_history import OrderStatusHistory
from app.models.product import Product
from app.models.user import User
from app.observability.metrics import metrics_registry
from app.schemas.order import CheckoutLineRead, CheckoutPreviewRead, OrderCheckoutCreate, OrderDocumentRead, OrderRefundRequest
from app.services.cart_service import CartService
from app.services.delivery_service import DeliveryService
from app.services.inventory_service import InventoryService
from app.services.payment_service import PaymentService

ORDER_STATUS_TRANSITIONS: dict[OrderStatusEnum, set[OrderStatusEnum]] = {
    OrderStatusEnum.CREATED: {
        OrderStatusEnum.AWAITING_PAYMENT,
        OrderStatusEnum.PAID,
        OrderStatusEnum.PROCESSING,
        OrderStatusEnum.CANCELLED,
        OrderStatusEnum.FAILED,
    },
    OrderStatusEnum.AWAITING_PAYMENT: {
        OrderStatusEnum.PAID,
        OrderStatusEnum.CANCELLED,
        OrderStatusEnum.FAILED,
    },
    OrderStatusEnum.PAID: {
        OrderStatusEnum.PROCESSING,
        OrderStatusEnum.CANCELLED,
        OrderStatusEnum.REFUNDED,
    },
    OrderStatusEnum.PROCESSING: {
        OrderStatusEnum.PACKED,
        OrderStatusEnum.CANCELLED,
    },
    OrderStatusEnum.PACKED: {
        OrderStatusEnum.SHIPPED,
        OrderStatusEnum.CANCELLED,
    },
    OrderStatusEnum.SHIPPED: {
        OrderStatusEnum.DELIVERED,
        OrderStatusEnum.CANCELLED,
    },
    OrderStatusEnum.DELIVERED: {
        OrderStatusEnum.REFUNDED,
    },
    OrderStatusEnum.FAILED: {
        OrderStatusEnum.AWAITING_PAYMENT,
        OrderStatusEnum.CANCELLED,
    },
    OrderStatusEnum.CANCELLED: set(),
    OrderStatusEnum.REFUNDED: set(),
}


class OrderService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.event_publisher = EventPublisher(session)
        self.cart_service = CartService(session)
        self.payment_service = PaymentService(session)
        self.inventory_service = InventoryService(session)
        self.delivery_service = DeliveryService(session)

    async def preview_checkout(self, user: User, checkout_data: OrderCheckoutCreate) -> CheckoutPreviewRead:
        cart_items = await self._get_cart_items(user.id)
        if not cart_items:
            raise ValueError("Cart is empty.")

        preview_items: list[CheckoutLineRead] = []
        items_total_amount = Decimal("0.00")

        for cart_item in cart_items:
            product = cart_item.product
            if not product or not product.is_active:
                raise ValueError("One of the cart items is no longer available.")
            if cart_item.quantity > self.inventory_service.get_available_stock(product):
                raise ValueError(f"Insufficient stock for product '{product.name}'.")

            line_total = (product.price * cart_item.quantity).quantize(Decimal("0.01"))
            items_total_amount += line_total
            preview_items.append(
                CheckoutLineRead(
                    product_id=product.id,
                    product_name=product.name,
                    quantity=cart_item.quantity,
                    unit_price=product.price,
                    line_total=line_total,
                )
            )

        quote = await self.delivery_service.calculate_quote(
            delivery_method=checkout_data.delivery_method,
            city=checkout_data.delivery_city,
            region=checkout_data.delivery_region,
            country=checkout_data.delivery_country,
            order_amount=items_total_amount,
            currency=checkout_data.currency,
        )
        total_amount = (items_total_amount + quote.cost).quantize(Decimal("0.01"))

        return CheckoutPreviewRead(
            items=preview_items,
            items_total_amount=items_total_amount.quantize(Decimal("0.01")),
            delivery_cost=quote.cost,
            total_amount=total_amount,
            currency=checkout_data.currency,
            delivery_method=checkout_data.delivery_method,
            payment_method=checkout_data.payment_method,
            calculated_at=datetime.now(timezone.utc),
        )

    async def create_from_cart(self, user: User, checkout_data: OrderCheckoutCreate) -> Order:
        cart_items = await self._get_cart_items(user.id)
        if not cart_items:
            raise ValueError("Cart is empty.")

        preview = await self.preview_checkout(user, checkout_data)
        now = datetime.now(timezone.utc)
        order = Order(
            user_id=user.id,
            status=OrderStatusEnum.CREATED,
            items_total_amount=preview.items_total_amount,
            delivery_cost=preview.delivery_cost,
            total_amount=preview.total_amount,
            price_locked_at=now,
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
            invoice_number=self._build_document_number(prefix="INV"),
        )
        self.session.add(order)
        await self.session.flush()
        self._record_status(
            order=order,
            from_status=None,
            to_status=OrderStatusEnum.CREATED,
            actor_user=user,
            reason="order_created",
        )

        reservation_items: list[tuple[Product, int]] = []
        for cart_item in cart_items:
            product = cart_item.product
            line_total = (product.price * cart_item.quantity).quantize(Decimal("0.01"))
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=cart_item.quantity,
                returned_quantity=0,
                line_total=line_total,
            )
            self.session.add(order_item)
            reservation_items.append((product, cart_item.quantity))

        await self.inventory_service.reserve_order_items(order_id=order.id, items=reservation_items)
        await self._publish_order_created(order)
        await self._publish_order_confirmed(order)

        previous_status = order.status
        await self.payment_service.create_checkout_payment(
            order,
            provider_name=checkout_data.payment_provider,
        )
        await self._handle_payment_side_effects(order, previous_status=previous_status, actor_user=user)

        await self.session.execute(delete(CartItem).where(CartItem.user_id == user.id))
        await self.session.commit()

        created_order = await self.get_by_id_for_user(user.id, order.id)
        if not created_order:
            raise ValueError("Unable to load created order.")

        metrics_registry.increment(
            "shop_orders_created_total",
            payment_method=created_order.payment_method.value,
            delivery_method=created_order.delivery_method.value,
        )
        return created_order

    async def retry_payment(
        self,
        user_id: UUID,
        order_id: UUID,
        *,
        idempotency_key: str | None = None,
    ) -> Order | None:
        order = await self.get_by_id_for_user(user_id, order_id)
        if not order:
            return None

        previous_status = order.status
        await self.payment_service.retry_payment(order, idempotency_key=idempotency_key)
        await self._handle_payment_side_effects(order, previous_status=previous_status)
        await self.session.commit()

        return await self.get_by_id_for_user(user_id, order_id)

    async def sync_payment_status(
        self,
        *,
        order_id: UUID,
        user_id: UUID | None = None,
        actor_user: User | None = None,
        idempotency_key: str | None = None,
    ) -> Order | None:
        order = await (self.get_by_id_for_user(user_id, order_id) if user_id else self.get_by_id(order_id))
        if not order:
            return None

        previous_status = order.status
        await self.payment_service.check_order_payment_status(order, idempotency_key=idempotency_key)
        await self._handle_payment_side_effects(order, previous_status=previous_status, actor_user=actor_user)
        await self.session.commit()

        return await self.get_by_id(order_id)

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
                selectinload(Order.status_history),
                selectinload(Order.delivery_shipments),
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
                selectinload(Order.status_history),
                selectinload(Order.delivery_shipments),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, order_id: UUID) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment_transactions),
                selectinload(Order.status_history),
                selectinload(Order.delivery_shipments),
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Order]:
        result = await self.session.execute(
            select(Order)
            .options(
                selectinload(Order.items),
                selectinload(Order.payment_transactions),
                selectinload(Order.status_history),
                selectinload(Order.delivery_shipments),
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        *,
        order_id: UUID,
        status: OrderStatusEnum,
        actor_user: User | None = None,
        reason: str | None = None,
    ) -> Order | None:
        order = await self.get_by_id(order_id)
        if not order:
            return None

        if status != order.status:
            allowed_statuses = ORDER_STATUS_TRANSITIONS.get(order.status, set())
            if status not in allowed_statuses:
                raise ValueError(
                    f"Cannot transition order from '{order.status.value}' to '{status.value}'."
                )

        previous_status = order.status
        refunded_amount: Decimal | None = None
        order.status = status

        if status == OrderStatusEnum.PAID:
            order.payment_status = PaymentStatusEnum.SUCCEEDED
            await self._finalize_paid_order(order)
        elif status == OrderStatusEnum.SHIPPED:
            await self.delivery_service.ensure_shipment(order)
        elif status == OrderStatusEnum.DELIVERED:
            await self.delivery_service.ensure_shipment(order)
            await self.payment_service.mark_offline_payment_succeeded(order)
            await self._finalize_paid_order(order)
        elif status == OrderStatusEnum.CANCELLED:
            order.cancellation_reason = reason
            refunded_amount = await self._cancel_order_internal(order, reason=reason)
        elif status == OrderStatusEnum.REFUNDED:
            refund_transaction = await self.payment_service.refund(order, reason=reason)
            refunded_amount = refund_transaction.amount
            refundable_items = [
                (item, item.quantity - item.returned_quantity)
                for item in order.items
                if item.quantity - item.returned_quantity > 0
            ]
            await self.inventory_service.return_order_items_to_stock(
                order_id=order.id,
                items=refundable_items,
                reason="full_refund",
            )
            for order_item, quantity in refundable_items:
                order_item.returned_quantity += quantity

        if status != previous_status or reason:
            self._record_status(
                order=order,
                from_status=previous_status,
                to_status=order.status,
                actor_user=actor_user,
                reason=reason,
            )

        if order.status == OrderStatusEnum.REFUNDED:
            await self._publish_order_refunded(
                order,
                refunded_amount=refunded_amount or order.total_amount,
                reason=reason,
            )
        else:
            await self._publish_order_status_transition(order, previous_status=previous_status, reason=reason)
            if refunded_amount is not None:
                await self._publish_order_refunded(order, refunded_amount=refunded_amount, reason=reason)

        await self.session.commit()
        return await self.get_by_id(order_id)

    async def cancel_order(
        self,
        *,
        order_id: UUID,
        user_id: UUID | None = None,
        actor_user: User | None = None,
        reason: str | None = None,
    ) -> Order | None:
        order = await (self.get_by_id_for_user(user_id, order_id) if user_id else self.get_by_id(order_id))
        if not order:
            return None

        if order.status in {OrderStatusEnum.CANCELLED, OrderStatusEnum.REFUNDED}:
            raise ValueError("Order is already closed.")

        previous_status = order.status
        order.status = OrderStatusEnum.CANCELLED
        order.cancellation_reason = reason
        refunded_amount = await self._cancel_order_internal(order, reason=reason)
        self._record_status(
            order=order,
            from_status=previous_status,
            to_status=OrderStatusEnum.CANCELLED,
            actor_user=actor_user,
            reason=reason,
        )
        await self._publish_order_status_transition(order, previous_status=previous_status, reason=reason)
        if refunded_amount is not None:
            await self._publish_order_refunded(order, refunded_amount=refunded_amount, reason=reason)
        await self.session.commit()

        return await self.get_by_id(order.id)

    async def refund_order(
        self,
        *,
        order_id: UUID,
        data: OrderRefundRequest,
        user_id: UUID | None = None,
        actor_user: User | None = None,
    ) -> Order | None:
        order = await (self.get_by_id_for_user(user_id, order_id) if user_id else self.get_by_id(order_id))
        if not order:
            return None
        if order.payment_status not in {
            PaymentStatusEnum.SUCCEEDED,
            PaymentStatusEnum.PARTIALLY_REFUNDED,
        }:
            raise ValueError("Order is not in refundable payment state.")

        refund_items: list[tuple[OrderItem, int]] = []
        refund_amount = Decimal("0.00")
        for request_item in data.items:
            order_item = next((item for item in order.items if item.id == request_item.order_item_id), None)
            if order_item is None:
                raise ValueError("Refund item was not found in order.")
            available_to_return = order_item.quantity - order_item.returned_quantity
            if request_item.quantity > available_to_return:
                raise ValueError("Refund quantity exceeds remaining returnable quantity.")
            refund_items.append((order_item, request_item.quantity))
            refund_amount += (order_item.unit_price * request_item.quantity).quantize(Decimal("0.01"))

        refund_transaction = await self.payment_service.refund(
            order,
            amount=refund_amount.quantize(Decimal("0.01")),
            reason=data.reason,
            idempotency_key=data.idempotency_key,
        )
        await self.inventory_service.return_order_items_to_stock(
            order_id=order.id,
            items=refund_items,
            reason="refund",
        )

        for order_item, quantity in refund_items:
            order_item.returned_quantity += quantity

        previous_status = order.status
        if self._all_items_returned(order):
            order.status = OrderStatusEnum.REFUNDED
        self._record_status(
            order=order,
            from_status=previous_status,
            to_status=order.status,
            actor_user=actor_user,
            reason=data.reason or ("partial_refund" if order.status != OrderStatusEnum.REFUNDED else "full_refund"),
        )
        await self._publish_order_refunded(
            order,
            refunded_amount=refund_transaction.amount,
            reason=data.reason,
        )

        await self.session.commit()
        return await self.get_by_id(order.id)

    async def reorder(self, *, user: User, order_id: UUID):
        order = await self.get_by_id_for_user(user.id, order_id)
        if not order:
            return None

        cart: object | None = None
        for item in order.items:
            if not item.product_id:
                continue
            quantity = item.quantity - item.returned_quantity
            if quantity <= 0:
                continue
            cart = await self.cart_service.add_item(
                user_id=user.id,
                product_id=item.product_id,
                quantity=quantity,
            )
        return cart

    async def build_document(self, *, order_id: UUID, document_type: str, user_id: UUID | None = None) -> OrderDocumentRead | None:
        order = await (self.get_by_id_for_user(user_id, order_id) if user_id else self.get_by_id(order_id))
        if not order:
            return None

        if document_type == "invoice":
            document_number = order.invoice_number or self._build_document_number(prefix="INV")
            if order.invoice_number is None:
                order.invoice_number = document_number
                await self.session.commit()
        elif document_type == "receipt":
            document_number = order.receipt_number or self._build_document_number(prefix="RCP")
            if order.receipt_number is None:
                order.receipt_number = document_number
                await self.session.commit()
        else:
            raise ValueError("Unsupported document type.")

        return OrderDocumentRead(
            document_type=document_type,
            document_number=document_number,
            order_id=order.id,
            issued_at=datetime.now(timezone.utc),
            amount=order.total_amount,
            currency=order.currency,
            items=order.items,
        )

    async def _get_cart_items(self, user_id: UUID) -> list[CartItem]:
        await self.session.execute(
            delete(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.expires_at <= datetime.now(timezone.utc),
            )
        )
        result = await self.session.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
            .order_by(CartItem.created_at)
        )
        return list(result.scalars().all())

    async def _handle_payment_side_effects(
        self,
        order: Order,
        *,
        previous_status: OrderStatusEnum,
        actor_user: User | None = None,
    ) -> None:
        if order.payment_status == PaymentStatusEnum.SUCCEEDED:
            await self._finalize_paid_order(order)
        elif order.payment_status in {PaymentStatusEnum.FAILED, PaymentStatusEnum.CANCELLED}:
            await self.inventory_service.release_order_reservations(
                order_id=order.id,
                reason="payment_unsuccessful",
            )

        if order.status != previous_status:
            self._record_status(
                order=order,
                from_status=previous_status,
                to_status=order.status,
                actor_user=actor_user,
                reason=f"payment_status:{order.payment_status.value}",
            )
            await self._publish_order_status_transition(
                order,
                previous_status=previous_status,
                reason=self._get_payment_failure_reason(order),
            )

    async def _finalize_paid_order(self, order: Order) -> None:
        await self.inventory_service.commit_order_reservations(
            order_id=order.id,
            reason="payment_captured",
        )
        if not order.receipt_number:
            order.receipt_number = self._build_document_number(prefix="RCP")

    async def _cancel_order_internal(self, order: Order, *, reason: str | None) -> Decimal | None:
        await self.inventory_service.release_order_reservations(
            order_id=order.id,
            reason="order_cancelled",
        )

        if order.payment_status == PaymentStatusEnum.PENDING:
            await self.payment_service.cancel_pending_payment(order)
            return None
        if order.payment_status in {
            PaymentStatusEnum.SUCCEEDED,
            PaymentStatusEnum.PARTIALLY_REFUNDED,
        }:
            refund_transaction = await self.payment_service.refund(order, reason=reason)
            refundable_items = [
                (item, item.quantity - item.returned_quantity)
                for item in order.items
                if item.quantity - item.returned_quantity > 0
            ]
            await self.inventory_service.return_order_items_to_stock(
                order_id=order.id,
                items=refundable_items,
                reason="cancelled_order",
            )
            for order_item, quantity in refundable_items:
                order_item.returned_quantity += quantity
            return refund_transaction.amount
        return None

    def _record_status(
        self,
        *,
        order: Order,
        from_status: OrderStatusEnum | None,
        to_status: OrderStatusEnum,
        actor_user: User | None,
        reason: str | None,
    ) -> None:
        self.session.add(
            OrderStatusHistory(
                order_id=order.id,
                from_status=from_status.value if from_status else None,
                to_status=to_status.value,
                actor_user_id=actor_user.id if actor_user else None,
                actor_role=actor_user.role.value if actor_user else None,
                reason=reason,
                details={
                    "payment_status": order.payment_status.value,
                    "total_amount": str(order.total_amount),
                },
            )
        )

    async def _publish_order_created(self, order: Order) -> None:
        await self.event_publisher.publish_domain(
            OrderCreated(
                order_id=str(order.id),
                user_id=str(order.user_id),
                total_amount=str(order.total_amount),
                currency=order.currency,
                payment_method=order.payment_method.value,
                delivery_method=order.delivery_method.value,
                customer_email=order.customer_email,
            )
        )

    async def _publish_order_confirmed(self, order: Order) -> None:
        await self.event_publisher.publish_domain(
            OrderConfirmed(
                order_id=str(order.id),
                user_id=str(order.user_id),
                customer_email=order.customer_email,
            )
        )

    async def _publish_order_status_transition(
        self,
        order: Order,
        *,
        previous_status: OrderStatusEnum,
        reason: str | None = None,
    ) -> None:
        if order.status == previous_status:
            return

        common_payload = {
            "order_id": str(order.id),
            "user_id": str(order.user_id),
            "customer_email": order.customer_email,
        }
        if order.status == OrderStatusEnum.PAID:
            await self.event_publisher.publish_domain(
                OrderPaid(
                    **common_payload,
                    payment_status=order.payment_status.value,
                    total_amount=str(order.total_amount),
                    currency=order.currency,
                )
            )
        elif order.status == OrderStatusEnum.FAILED:
            await self.event_publisher.publish_domain(
                OrderPaymentFailed(
                    **common_payload,
                    total_amount=str(order.total_amount),
                    currency=order.currency,
                    reason=reason or self._get_payment_failure_reason(order),
                )
            )
        elif order.status == OrderStatusEnum.PROCESSING:
            await self.event_publisher.publish_domain(OrderProcessingStarted(**common_payload))
        elif order.status == OrderStatusEnum.PACKED:
            await self.event_publisher.publish_domain(OrderPacked(**common_payload))
        elif order.status == OrderStatusEnum.SHIPPED:
            await self.event_publisher.publish_domain(
                OrderShipped(
                    **common_payload,
                    tracking_number=self._get_tracking_number(order),
                )
            )
        elif order.status == OrderStatusEnum.DELIVERED:
            await self.event_publisher.publish_domain(OrderDelivered(**common_payload))
        elif order.status == OrderStatusEnum.CANCELLED:
            await self.event_publisher.publish_domain(
                OrderCancelled(
                    **common_payload,
                    reason=reason,
                )
            )

    async def _publish_order_refunded(
        self,
        order: Order,
        *,
        refunded_amount: Decimal,
        reason: str | None = None,
    ) -> None:
        await self.event_publisher.publish_domain(
            OrderRefunded(
                order_id=str(order.id),
                user_id=str(order.user_id),
                customer_email=order.customer_email,
                refunded_amount=str(refunded_amount.quantize(Decimal("0.01"))),
                currency=order.currency,
                reason=reason,
            )
        )

    @staticmethod
    def _get_tracking_number(order: Order) -> str | None:
        if not order.delivery_shipments:
            return None
        return order.delivery_shipments[-1].tracking_number

    @staticmethod
    def _get_payment_failure_reason(order: Order) -> str | None:
        if not order.payment_transactions:
            return None
        return order.payment_transactions[-1].failure_reason

    @staticmethod
    def _all_items_returned(order: Order) -> bool:
        return all(item.returned_quantity >= item.quantity for item in order.items)

    @staticmethod
    def _build_document_number(*, prefix: str) -> str:
        return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
