from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.plan import PremiumPlan


class PlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_active(self) -> list[PremiumPlan]:
        stmt = (
            select(PremiumPlan)
            .where(PremiumPlan.is_active.is_(True))
            .order_by(PremiumPlan.sort_order)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self) -> list[PremiumPlan]:
        result = await self.session.execute(select(PremiumPlan).order_by(PremiumPlan.sort_order))
        return list(result.scalars().all())

    async def get(self, plan_id: int) -> PremiumPlan | None:
        result = await self.session.execute(select(PremiumPlan).where(PremiumPlan.id == plan_id))
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> PremiumPlan | None:
        result = await self.session.execute(select(PremiumPlan).where(PremiumPlan.code == code))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PremiumPlan:
        plan = PremiumPlan(**kwargs)
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def update(self, plan: PremiumPlan, **kwargs) -> PremiumPlan:
        for k, v in kwargs.items():
            setattr(plan, k, v)
        await self.session.flush()
        return plan
