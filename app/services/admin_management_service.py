"""Runtime management of tier-2 ("granted") in-Telegram admins.

This is the service backing the admin panel's "👑 Admins" section
(`app.bot.handlers.admin.admins`). It never touches `TELEGRAM_SUPERADMIN_IDS`
itself -- that env var remains the tier-1 "owner" list, editable only by
whoever controls the deployment's environment/`.env` file and a process
restart. This service only manages the `admin_grants` DB table (tier 2),
which is exactly what lets an owner add/remove co-administrators without
touching `.env` or restarting anything.

Caller responsibility: every method here assumes the CALLER has already
verified the acting user is an owner (`app.core.admin_access.is_owner_admin`)
-- this service does not re-check that itself, exactly like every other
admin-panel service (`GiftService`, `BloggerService`, etc.) trusts the
handler layer's `AdminAccessFilter` to have already gated the request.
"""

from __future__ import annotations

from app.db.models.admin_grant import AdminGrant
from app.db.uow import UnitOfWork


class AdminManagementService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def list_grants(self, *, active_only: bool = False) -> list[AdminGrant]:
        if active_only:
            return await self.uow.admin_grants.list_active()
        return await self.uow.admin_grants.list_all()

    async def grant(
        self, *, telegram_id: int, granted_by_telegram_id: int, label: str | None = None
    ) -> AdminGrant:
        if telegram_id == granted_by_telegram_id:
            raise ValueError("An owner cannot grant admin access to themselves via this flow")
        return await self.uow.admin_grants.grant(
            telegram_id=telegram_id, granted_by_telegram_id=granted_by_telegram_id, label=label
        )

    async def revoke(self, telegram_id: int, *, revoked_by_telegram_id: int) -> AdminGrant | None:
        grant = await self.uow.admin_grants.get_by_telegram_id(telegram_id)
        if grant is None or not grant.is_active:
            return None
        await self.uow.admin_grants.revoke(grant, revoked_by_telegram_id=revoked_by_telegram_id)
        return grant
