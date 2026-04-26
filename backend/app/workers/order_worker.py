from __future__ import annotations

import asyncio

from app.workers.runtime import run_rabbitmq_subscriber_worker


def main() -> None:
    asyncio.run(
        run_rabbitmq_subscriber_worker(
            worker_name="order-worker",
            queue_name="shop.events.orders",
            routing_keys=[
                "shop.CRMOrderSyncRequested",
                "shop.ERPOrderSyncRequested",
                "shop.ReceiptGenerationRequested",
            ],
        )
    )


if __name__ == "__main__":
    main()
