from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete

from app.db.postgres import db_postgres
from app.models.cart_item import CartItem
from app.services.auth_service import AuthService
from app.workers.runtime import run_periodic_worker


async def process_once() -> int:
    async with db_postgres.session_factory() as session:
        await AuthService(session).cleanup_expired_tokens()
        result = await session.execute(
            delete(CartItem).where(CartItem.expires_at <= datetime.now(timezone.utc))
        )
        await session.commit()
        return int(getattr(result, "rowcount", 0) or 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run cleanup worker.")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if args.once:
        asyncio.run(process_once())
        return
    asyncio.run(run_periodic_worker(worker_name="cleanup-worker", process_once=process_once))


if __name__ == "__main__":
    main()
