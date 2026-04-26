from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.domain_events import (
    InventoryCommitted,
    InventoryReleased,
    InventoryReservationFailed,
    InventoryReserved,
    StockChanged,
)
from app.events.publishers.event_publisher import EventPublisher
from app.models.inventory_reservation import InventoryReservation
from app.models.order_item import OrderItem
from app.models.product import Product


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.event_publisher = EventPublisher(session)

    @staticmethod
    def get_available_stock(product: Product) -> int:
        return max(product.stock - product.reserved_stock, 0)

    async def reserve_order_items(
        self,
        *,
        order_id: UUID,
        items: Iterable[tuple[Product, int]],
    ) -> list[InventoryReservation]:
        reservations: list[InventoryReservation] = []
        for product, quantity in items:
            if quantity > self.get_available_stock(product):
                await self.event_publisher.publish_domain(
                    InventoryReservationFailed(
                        product_id=str(product.id),
                        order_id=str(order_id),
                        requested_quantity=quantity,
                        available_stock=self.get_available_stock(product),
                    )
                )
                raise ValueError(f"Insufficient stock for product '{product.name}'.")

            product.reserved_stock += quantity
            reservation = InventoryReservation(
                order_id=order_id,
                product_id=product.id,
                quantity=quantity,
                status="active",
                reason="order",
            )
            self.session.add(reservation)
            reservations.append(reservation)
            await self.event_publisher.publish_domain(
                InventoryReserved(
                    product_id=str(product.id),
                    order_id=str(order_id),
                    quantity=quantity,
                    stock=product.stock,
                    reserved_stock=product.reserved_stock,
                )
            )
            await self._publish_stock_changed(product, reason="reserved")
        return reservations

    async def release_order_reservations(
        self,
        *,
        order_id: UUID,
        reason: str = "released",
    ) -> list[InventoryReservation]:
        result = await self.session.execute(
            select(InventoryReservation)
            .where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == "active",
            )
            .with_for_update()
        )
        reservations = list(result.scalars().all())
        for reservation in reservations:
            product = reservation.product
            product.reserved_stock = max(product.reserved_stock - reservation.quantity, 0)
            reservation.status = "released"
            reservation.reason = reason
            await self.event_publisher.publish_domain(
                InventoryReleased(
                    product_id=str(product.id),
                    order_id=str(order_id),
                    quantity=reservation.quantity,
                    stock=product.stock,
                    reserved_stock=product.reserved_stock,
                )
            )
            await self._publish_stock_changed(product, reason=reason)
        return reservations

    async def commit_order_reservations(
        self,
        *,
        order_id: UUID,
        reason: str = "committed",
    ) -> list[InventoryReservation]:
        result = await self.session.execute(
            select(InventoryReservation)
            .where(
                InventoryReservation.order_id == order_id,
                InventoryReservation.status == "active",
            )
            .with_for_update()
        )
        reservations = list(result.scalars().all())
        for reservation in reservations:
            product = reservation.product
            if reservation.quantity > product.reserved_stock:
                raise ValueError(f"Reservation drift detected for product '{product.name}'.")
            if reservation.quantity > product.stock:
                raise ValueError(f"Cannot commit stock for product '{product.name}'.")
            product.reserved_stock -= reservation.quantity
            product.stock -= reservation.quantity
            reservation.status = "committed"
            reservation.reason = reason
            await self.event_publisher.publish_domain(
                InventoryCommitted(
                    product_id=str(product.id),
                    order_id=str(order_id),
                    quantity=reservation.quantity,
                    stock=product.stock,
                    reserved_stock=product.reserved_stock,
                )
            )
            await self._publish_stock_changed(product, reason=reason)
        return reservations

    async def return_order_items_to_stock(
        self,
        *,
        order_id: UUID,
        items: Iterable[tuple[OrderItem, int]],
        reason: str = "returned",
    ) -> list[InventoryReservation]:
        restocked: list[InventoryReservation] = []
        for order_item, quantity in items:
            if not order_item.product_id:
                continue
            product = await self.session.get(Product, order_item.product_id)
            if not product:
                continue
            product.stock += quantity
            reservation = InventoryReservation(
                order_id=order_id,
                product_id=product.id,
                quantity=quantity,
                status="returned",
                reason=reason,
            )
            self.session.add(reservation)
            restocked.append(reservation)
            await self._publish_stock_changed(product, reason=reason)
        return restocked

    async def _publish_stock_changed(self, product: Product, *, reason: str) -> None:
        await self.event_publisher.publish_domain(
            StockChanged(
                product_id=str(product.id),
                stock=product.stock,
                reserved_stock=product.reserved_stock,
                available_stock=self.get_available_stock(product),
                reason=reason,
            )
        )
