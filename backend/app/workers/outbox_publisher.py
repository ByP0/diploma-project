from __future__ import annotations

import asyncio

from app.core.config import setting
from app.db.postgres import db_postgres
from app.events.outbox.dispatcher import OutboxDispatcher
from app.workers.runtime import run_periodic_worker


async def process_once() -> int:
    async with db_postgres.session_factory() as session:
        return await OutboxDispatcher(session).dispatch_pending(limit=setting.worker_batch_size)


def main() -> None:
    asyncio.run(run_periodic_worker(worker_name="outbox-publisher", process_once=process_once))


if __name__ == "__main__":
    main()
