from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.referral import Referral


class ReferralRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_referred_user(self, referred_user_id: int) -> Referral | None:
        result = await self.session.execute(
            select(Referral).where(Referral.referred_user_id == referred_user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        referred_user_id: int,
        referrer_user_id: int,
        is_self_referral: bool = False,
        is_suspicious: bool = False,
        suspicious_reason: str | None = None,
        referrer_was_blogger_at_join: bool = False,
    ) -> Referral:
        referral = Referral(
            referred_user_id=referred_user_id,
            referrer_user_id=referrer_user_id,
            attributed_at=dt.datetime.now(dt.UTC),
            is_self_referral=is_self_referral,
            is_suspicious=is_suspicious,
            suspicious_reason=suspicious_reason,
            referrer_was_blogger_at_join=referrer_was_blogger_at_join,
        )
        self.session.add(referral)
        await self.session.flush()
        return referral

    async def mark_qualified(self, referral: Referral) -> None:
        referral.is_qualified = True
        referral.qualified_at = dt.datetime.now(dt.UTC)
        await self.session.flush()

    async def mark_disqualified(self, referral: Referral, reason: str) -> None:
        referral.is_qualified = False
        referral.disqualified_reason = reason
        await self.session.flush()

    async def count_referrals_for_referrer(self, referrer_user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_user_id == referrer_user_id)
        )
        return int(result.scalar_one())

    async def count_qualified_for_referrer(self, referrer_user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_user_id == referrer_user_id, Referral.is_qualified.is_(True)
            )
        )
        return int(result.scalar_one())

    async def list_for_referrer(
        self, referrer_user_id: int, limit: int = 50, offset: int = 0
    ) -> list[Referral]:
        stmt = (
            select(Referral)
            .where(Referral.referrer_user_id == referrer_user_id)
            .order_by(Referral.attributed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_suspicious(self, limit: int = 50, offset: int = 0) -> list[Referral]:
        stmt = (
            select(Referral)
            .where(Referral.is_suspicious.is_(True))
            .order_by(Referral.attributed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_suspicious(self) -> int:
        result = await self.session.execute(
            select(func.count(Referral.id)).where(Referral.is_suspicious.is_(True))
        )
        return int(result.scalar_one())
