from __future__ import annotations

import asyncio

from app.workers.runtime import run_rabbitmq_subscriber_worker


def main() -> None:
    asyncio.run(
        run_rabbitmq_subscriber_worker(
            worker_name="analytics-worker",
            queue_name="shop.events.analytics",
            routing_keys=["shop.AnalyticsSyncRequested"],
        )
    )


if __name__ == "__main__":
    main()
