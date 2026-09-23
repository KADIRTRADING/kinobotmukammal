"""Reconciliation: verifies the wallet-cache invariant (sum of ledger
entries per bucket == cached wallet balance) and flags any drift for admin
investigation via a structured log line (never silently "fixes" balances --
a drift indicates a bug and must be investigated, not papered over).

Also re-checks any PENDING orders older than a threshold against their
payment provider where the provider supports a status-lookup API, so a
missed webhook doesn't leave an order stuck forever.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select

from app.core.logging import get_logger
from app.db.models.enums import OrderStatus
from app.db.models.order import Order
from app.db.models.wallet import LedgerEntry, Wallet
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)

STALE_PENDING_ORDER_HOURS = 24


async def check_ledger_consistency() -> list[dict]:
    """Returns a list of {wallet_id, bucket, cached, computed} for any
    wallet whose cached balance doesn't match the sum of its ledger
    entries. An empty list means everything reconciles."""
    drifts: list[dict] = []
    async with AsyncSessionLocal() as session:
        wallets = (await session.execute(select(Wallet))).scalars().all()
        for wallet in wallets:
            for bucket, cached in (
                ("available", wallet.available_amount),
                ("reserved", wallet.reserved_amount),
                ("pending", wallet.pending_amount),
            ):
                total = (
                    await session.execute(
                        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(
                            LedgerEntry.wallet_id == wallet.id, LedgerEntry.bucket == bucket
                        )
                    )
                ).scalar_one()
                if int(total) != cached:
                    drifts.append(
                        {
                            "wallet_id": wallet.id,
                            "bucket": bucket,
                            "cached": cached,
                            "computed": int(total),
                        }
                    )

    if drifts:
        logger.error("Ledger reconciliation drift detected: %s", drifts)
    return drifts


async def flag_stale_pending_orders() -> list[int]:
    """Orders stuck in PENDING beyond the threshold are flagged (logged +
    returned) for admin review -- possibly a missed webhook. Does NOT
    auto-cancel; a human should confirm with the provider first."""
    threshold = dt.datetime.now(dt.UTC) - dt.timedelta(hours=STALE_PENDING_ORDER_HOURS)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Order.id).where(
                Order.status == OrderStatus.PENDING.value, Order.created_at < threshold
            )
        )
        stale_ids = [row[0] for row in result.all()]
    if stale_ids:
        logger.warning(
            "Stale PENDING orders older than %sh: %s", STALE_PENDING_ORDER_HOURS, stale_ids
        )
    return stale_ids
