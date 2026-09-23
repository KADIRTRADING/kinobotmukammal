from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.reward_accrual import BloggerAcquisitionReward, ReferralCommission


class RewardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Referral commissions ---------------------------------------------------
    async def get_commission_by_order(self, order_id: int) -> ReferralCommission | None:
        result = await self.session.execute(
            select(ReferralCommission).where(ReferralCommission.order_id == order_id)
        )
        return result.scalar_one_or_none()

    async def create_commission(self, **kwargs) -> ReferralCommission:
        commission = ReferralCommission(**kwargs)
        self.session.add(commission)
        await self.session.flush()
        return commission

    async def list_for_referrer(
        self, referrer_user_id: int, limit: int = 50
    ) -> list[ReferralCommission]:
        stmt = (
            select(ReferralCommission)
            .where(ReferralCommission.referrer_user_id == referrer_user_id)
            .order_by(ReferralCommission.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Blogger acquisition rewards ---------------------------------------------
    async def get_reward_by_referral(self, referral_id: int) -> BloggerAcquisitionReward | None:
        result = await self.session.execute(
            select(BloggerAcquisitionReward).where(
                BloggerAcquisitionReward.referral_id == referral_id
            )
        )
        return result.scalar_one_or_none()

    async def create_reward(self, **kwargs) -> BloggerAcquisitionReward:
        reward = BloggerAcquisitionReward(**kwargs)
        self.session.add(reward)
        await self.session.flush()
        return reward

    async def list_for_blogger(
        self, blogger_user_id: int, limit: int = 50
    ) -> list[BloggerAcquisitionReward]:
        stmt = (
            select(BloggerAcquisitionReward)
            .where(BloggerAcquisitionReward.blogger_user_id == blogger_user_id)
            .order_by(BloggerAcquisitionReward.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
