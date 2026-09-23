from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.gift import Gift


class GiftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Gift:
        gift = Gift(**kwargs)
        self.session.add(gift)
        await self.session.flush()
        return gift

    async def list_received(self, user_id: int, limit: int = 50) -> list[Gift]:
        stmt = (
            select(Gift)
            .where(Gift.recipient_user_id == user_id)
            .order_by(Gift.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_sent(self, user_id: int, limit: int = 50) -> list[Gift]:
        stmt = (
            select(Gift)
            .where(Gift.sender_user_id == user_id)
            .order_by(Gift.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
