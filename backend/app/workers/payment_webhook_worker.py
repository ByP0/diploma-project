from __future__ import annotations

import asyncio

from app.workers.runtime import run_rabbitmq_subscriber_worker


def main() -> None:
    asyncio.run(
        run_rabbitmq_subscriber_worker(
            worker_name="payment-webhook-worker",
            queue_name="shop.events.payment-webhooks",
            routing_keys=["shop.BackgroundTaskRequested"],
        )
    )


if __name__ == "__main__":
    main()
