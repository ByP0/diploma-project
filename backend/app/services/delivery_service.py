from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4, UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.events.domain_events import OrderDelivered, ShipmentCreated, ShipmentDelivered, ShipmentFailed, ShipmentTrackingUpdated
from app.events.publishers.event_publisher import EventPublisher
from app.models.delivery_address import DeliveryAddress
from app.models.delivery_shipment import DeliveryShipment
from app.models.order import DeliveryMethodEnum, Order, OrderStatusEnum


@dataclass(slots=True)
class DeliveryQuote:
    provider_name: str
    delivery_method: DeliveryMethodEnum
    cost: Decimal
    currency: str
    estimated_days: int
    details: dict[str, str]


class DeliveryService:
    provider_name = "stub_delivery"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.event_publisher = EventPublisher(session)

    async def calculate_quote(
        self,
        *,
        delivery_method: DeliveryMethodEnum,
        city: str | None,
        region: str | None,
        country: str,
        order_amount: Decimal,
        currency: str = "RUB",
    ) -> DeliveryQuote:
        if delivery_method == DeliveryMethodEnum.PICKUP:
            return DeliveryQuote(
                provider_name=self.provider_name,
                delivery_method=delivery_method,
                cost=Decimal("0.00"),
                currency=currency,
                estimated_days=0,
                details={"service_level": "pickup"},
            )

        base_cost = Decimal("199.00") if delivery_method == DeliveryMethodEnum.COURIER else Decimal("399.00")
        if order_amount >= Decimal("5000.00") and delivery_method == DeliveryMethodEnum.COURIER:
            base_cost = Decimal("0.00")
        if city and city.lower() not in {"kaliningrad", "калининград"}:
            base_cost += Decimal("150.00")
        if country.upper() != "RU":
            base_cost += Decimal("500.00")

        estimated_days = 1 if delivery_method == DeliveryMethodEnum.EXPRESS else 2
        if region and region.lower() not in {"калининградская область", "kaliningrad region"}:
            estimated_days += 1

        return DeliveryQuote(
            provider_name=self.provider_name,
            delivery_method=delivery_method,
            cost=base_cost,
            currency=currency,
            estimated_days=estimated_days,
            details={"city": city or "", "region": region or ""},
        )

    async def ensure_shipment(self, order: Order) -> DeliveryShipment:
        shipment_created = False
        if order.delivery_shipments:
            shipment = order.delivery_shipments[-1]
        else:
            shipment_created = True
            shipment = DeliveryShipment(
                order_id=order.id,
                provider_name=self.provider_name,
                delivery_method=order.delivery_method,
                status="created",
                quoted_cost=order.delivery_cost,
                external_delivery_id=f"dlv_{uuid4().hex[:16]}",
                tracking_number=f"TRK-{uuid4().hex[:12].upper()}",
                request_payload={
                    "order_id": str(order.id),
                    "delivery_method": order.delivery_method.value,
                },
                response_payload={"mode": "stub_created"},
            )
            self.session.add(shipment)
            order.delivery_shipments.append(shipment)

        previous_status = shipment.status if not shipment_created else None
        previous_tracking_number = shipment.tracking_number
        if order.status == OrderStatusEnum.PACKED:
            shipment.status = "packed"
        elif order.status == OrderStatusEnum.SHIPPED:
            shipment.status = "in_transit"
            shipment.shipped_at = datetime.now(timezone.utc)
        elif order.status == OrderStatusEnum.DELIVERED:
            shipment.status = "delivered"
            shipment.delivered_at = datetime.now(timezone.utc)
        elif order.status == OrderStatusEnum.CANCELLED:
            shipment.status = "cancelled"

        await self._publish_shipment_events(
            shipment,
            previous_status=previous_status,
            previous_tracking_number=previous_tracking_number,
            created=shipment_created,
        )
        return shipment

    async def apply_webhook(
        self,
        *,
        provider_name: str,
        external_delivery_id: str | None,
        tracking_number: str | None,
        status: str,
        delivered: bool,
    ) -> DeliveryShipment | None:
        if provider_name != self.provider_name:
            raise ValueError(f"Unsupported delivery provider '{provider_name}'.")

        filters = []
        if external_delivery_id:
            filters.append(DeliveryShipment.external_delivery_id == external_delivery_id)
        if tracking_number:
            filters.append(DeliveryShipment.tracking_number == tracking_number)
        if not filters:
            raise ValueError("Either external_delivery_id or tracking_number is required.")

        result = await self.session.execute(select(DeliveryShipment).where(*filters))
        shipment = result.scalar_one_or_none()
        if not shipment:
            return None

        payload = shipment.response_payload or {}
        if (
            shipment.provider_name == provider_name
            and payload.get("webhook_status") == status
            and bool(payload.get("webhook_delivered")) == delivered
        ):
            return shipment

        previous_status = shipment.status
        previous_order_status = shipment.order.status
        previous_tracking_number = shipment.tracking_number
        shipment.status = status
        shipment.response_payload = {
            **payload,
            "webhook_status": status,
            "webhook_delivered": delivered,
        }
        if delivered:
            shipment.delivered_at = datetime.now(timezone.utc)
            shipment.order.status = OrderStatusEnum.DELIVERED
            if previous_order_status != OrderStatusEnum.DELIVERED:
                await self.event_publisher.publish_domain(
                    OrderDelivered(
                        order_id=str(shipment.order.id),
                        user_id=str(shipment.order.user_id),
                        customer_email=shipment.order.customer_email,
                    )
                )
        await self._publish_shipment_events(
            shipment,
            previous_status=previous_status,
            previous_tracking_number=previous_tracking_number,
            created=False,
        )
        await self.session.commit()
        return shipment

    async def list_addresses(self, *, user_id: UUID) -> list[DeliveryAddress]:
        result = await self.session.execute(
            select(DeliveryAddress)
            .where(DeliveryAddress.user_id == user_id)
            .order_by(DeliveryAddress.is_default.desc(), DeliveryAddress.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_address(self, *, user_id: UUID, data: dict[str, object]) -> DeliveryAddress:
        if data.get("is_default"):
            await self.session.execute(
                update(DeliveryAddress)
                .where(DeliveryAddress.user_id == user_id, DeliveryAddress.is_default.is_(True))
                .values(is_default=False)
            )

        address = DeliveryAddress(user_id=user_id, **data)
        self.session.add(address)
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def update_address(
        self,
        *,
        user_id: UUID,
        address_id: UUID,
        data: dict[str, object],
    ) -> DeliveryAddress | None:
        address = await self.session.get(DeliveryAddress, address_id)
        if not address or address.user_id != user_id:
            return None

        if data.get("is_default"):
            await self.session.execute(
                update(DeliveryAddress)
                .where(DeliveryAddress.user_id == user_id, DeliveryAddress.id != address_id)
                .values(is_default=False)
            )

        for field_name, value in data.items():
            setattr(address, field_name, value)

        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def delete_address(self, *, user_id: UUID, address_id: UUID) -> bool:
        address = await self.session.get(DeliveryAddress, address_id)
        if not address or address.user_id != user_id:
            return False

        await self.session.delete(address)
        await self.session.commit()
        return True

    async def _publish_shipment_events(
        self,
        shipment: DeliveryShipment,
        *,
        previous_status: str | None,
        previous_tracking_number: str | None,
        created: bool,
    ) -> None:
        if created:
            await self.event_publisher.publish_domain(
                ShipmentCreated(
                    shipment_id=str(shipment.id),
                    order_id=str(shipment.order_id),
                    provider_name=shipment.provider_name,
                    tracking_number=shipment.tracking_number,
                )
            )

        if created or previous_status != shipment.status or previous_tracking_number != shipment.tracking_number:
            await self.event_publisher.publish_domain(
                ShipmentTrackingUpdated(
                    shipment_id=str(shipment.id),
                    order_id=str(shipment.order_id),
                    provider_name=shipment.provider_name,
                    tracking_number=shipment.tracking_number,
                    status=shipment.status,
                )
            )

        if shipment.status == "delivered" and previous_status != "delivered":
            await self.event_publisher.publish_domain(
                ShipmentDelivered(
                    shipment_id=str(shipment.id),
                    order_id=str(shipment.order_id),
                    provider_name=shipment.provider_name,
                )
            )
        elif shipment.status in {"failed", "cancelled"} and previous_status != shipment.status:
            await self.event_publisher.publish_domain(
                ShipmentFailed(
                    shipment_id=str(shipment.id),
                    order_id=str(shipment.order_id),
                    provider_name=shipment.provider_name,
                    status=shipment.status,
                )
            )
