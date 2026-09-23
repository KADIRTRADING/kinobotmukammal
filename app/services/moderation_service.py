"""Admin moderation queues: suspicious referrals, pending promo attribution
links, and pending blogger applications, gathered in one place for the
admin panel's review screens.
"""

from __future__ import annotations

from app.db.uow import UnitOfWork


class ModerationService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def suspicious_referrals(self, limit: int = 50):
        return await self.uow.referrals.list_suspicious(limit=limit)

    async def pending_promo_links(self, limit: int = 50):
        return await self.uow.promos.list_pending_moderation(limit=limit)

    async def pending_blogger_applications(self, limit: int = 50):
        return await self.uow.bloggers.list_pending(limit=limit)

    async def open_support_tickets(self, limit: int = 50):
        return await self.uow.support.list_open(limit=limit)
