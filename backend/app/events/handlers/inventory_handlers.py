from __future__ import annotations

from app.core.config import setting
from app.events.domain_events.inventory_events import LowStockDetected, StockChanged
from app.events.event_bus.base import EventContext


async def handle_stock_changed(event: StockChanged, context: EventContext) -> None:
    if event.available_stock > setting.events_low_stock_threshold:
        return

    await context.publisher.publish_domain(
        LowStockDetected(
            product_id=event.product_id,
            stock=event.stock,
            reserved_stock=event.reserved_stock,
            available_stock=event.available_stock,
            threshold=setting.events_low_stock_threshold,
        )
    )
