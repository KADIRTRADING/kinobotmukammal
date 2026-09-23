"""Scheduled-job entrypoint for the `worker` docker-compose service.

Runs every background job on its own APScheduler interval, sharing one
long-lived `aiogram.Bot` instance (needed for broadcast sending). Started
via `python -m app.workers.runner`.
"""

from __future__ import annotations

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot.factory import build_bot
from app.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.workers.broadcast_worker import process_pending_broadcasts
from app.workers.expiration_worker import release_expired_promo_codes
from app.workers.reconciliation_worker import check_ledger_consistency, flag_stale_pending_orders

settings = get_settings()
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)


async def run_workers() -> None:
    bot = build_bot(settings)
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        process_pending_broadcasts,
        "interval",
        seconds=10,
        args=[bot],
        id="broadcast_worker",
        max_instances=1,
    )
    scheduler.add_job(
        release_expired_promo_codes, "interval", minutes=15, id="expiration_worker", max_instances=1
    )
    scheduler.add_job(
        check_ledger_consistency,
        "interval",
        minutes=30,
        id="ledger_reconciliation",
        max_instances=1,
    )
    scheduler.add_job(
        flag_stale_pending_orders, "interval", hours=1, id="stale_order_check", max_instances=1
    )

    scheduler.start()
    logger.info("Worker scheduler started")

    try:
        await asyncio.Event().wait()  # run forever
    finally:
        scheduler.shutdown()
        await bot.session.close()


def main() -> None:
    asyncio.run(run_workers())


if __name__ == "__main__":
    main()
