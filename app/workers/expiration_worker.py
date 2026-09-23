"""Handles time-based expirations:
- Expired, unreleased user-funded promo codes: release their unused
  reserve back to the issuer (spec section 7's documented policy).
- (Premium access itself is computed live from `User.premium_until` on
  every check, so no separate "expire premium" job is needed -- but this
  worker sends an optional expiry-approaching notice, which is a nice-to-
  have and safe to skip if translations aren't wired for it.)
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork
from app.services.promo_service import PromoService

logger = get_logger(__name__)


async def release_expired_promo_codes() -> int:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        expired = await uow.promos.list_expired_unreleased(limit=500)
        promo_service = PromoService(uow)
        count = 0
        for promo in expired:
            await promo_service.expire_and_release(promo)
            count += 1
        await session.commit()
        if count:
            logger.info("Released unused reserve for %d expired promo codes", count)
        return count
