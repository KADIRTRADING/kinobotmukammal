from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.admin_grant import AdminGrant


class AdminGrantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> AdminGrant | None:
        result = await self.session.execute(
            select(AdminGrant).where(AdminGrant.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[AdminGrant]:
        result = await self.session.execute(
            select(AdminGrant)
            .where(AdminGrant.is_active.is_(True))
            .order_by(AdminGrant.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[AdminGrant]:
        """Includes revoked grants -- used by the admin panel's history
        view so a revocation is never silently forgotten."""
        result = await self.session.execute(
            select(AdminGrant).order_by(AdminGrant.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_active_telegram_ids(self) -> frozenset[int]:
        """Cheap set of currently-granted Telegram ids, used by
        `AdminAccessFilter` on every admin message/callback. Kept as its
        own narrow query (rather than reusing `list_active` +
        list-comprehension by the caller) so it's obvious this is the hot
        path that runs on every single admin-panel interaction."""
        result = await self.session.execute(
            select(AdminGrant.telegram_id).where(AdminGrant.is_active.is_(True))
        )
        return frozenset(result.scalars().all())

    async def grant(
        self, *, telegram_id: int, granted_by_telegram_id: int, label: str | None = None
    ) -> AdminGrant:
        """Creates a new grant, or reactivates + relabels an existing
        (possibly revoked) row for the same `telegram_id` -- never creates
        a duplicate row for the same id, since `telegram_id` is unique."""
        existing = await self.get_by_telegram_id(telegram_id)
        if existing is not None:
            existing.is_active = True
            existing.granted_by_telegram_id = granted_by_telegram_id
            existing.revoked_by_telegram_id = None
            existing.revoked_at = None
            if label:
                existing.label = label
            await self.session.flush()
            return existing

        grant = AdminGrant(
            telegram_id=telegram_id,
            label=label,
            granted_by_telegram_id=granted_by_telegram_id,
            is_active=True,
        )
        self.session.add(grant)
        await self.session.flush()
        return grant

    async def revoke(self, grant: AdminGrant, *, revoked_by_telegram_id: int) -> None:
        grant.is_active = False
        grant.revoked_by_telegram_id = revoked_by_telegram_id
        grant.revoked_at = dt.datetime.now(dt.UTC)
        await self.session.flush()
