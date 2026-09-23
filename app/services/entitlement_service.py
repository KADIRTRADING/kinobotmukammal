"""Grants premium entitlements exactly once per (source, source_reference).

This is the single choke point that extends `User.premium_until` -- called
after a verified payment, an approved gift, or a redeemed full-premium
promo code. The unique constraint on `Entitlement(source, source_reference)`
plus an explicit pre-check here means retried webhooks or double-clicks
can never grant premium twice for the same underlying event.
"""

from __future__ import annotations

import datetime as dt

from app.db.models.enums import EntitlementSource
from app.db.uow import UnitOfWork


class EntitlementService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def grant(
        self,
        *,
        user_id: int,
        plan_id: int,
        duration_days: int,
        source: EntitlementSource,
        source_reference: str,
        granted_by_admin_id: int | None = None,
        reason: str | None = None,
    ):
        existing = await self.uow.orders.get_entitlement_by_source(source.value, source_reference)
        if existing is not None:
            return existing  # idempotent: already granted for this exact event

        user = await self.uow.users.get_by_id(user_id)
        if user is None:
            raise ValueError(f"user {user_id} not found")

        now = dt.datetime.now(dt.UTC)
        base = user.premium_until if (user.premium_until and user.premium_until > now) else now
        ends_at = base + dt.timedelta(days=duration_days)

        entitlement = await self.uow.orders.create_entitlement(
            user_id=user_id,
            plan_id=plan_id,
            source=source.value,
            source_reference=source_reference,
            starts_at=now,
            ends_at=ends_at,
            granted_by_admin_id=granted_by_admin_id,
            reason=reason,
        )
        await self.uow.users.grant_premium_until(user, ends_at)
        return entitlement

    async def revoke_future(self, user_id: int) -> None:
        """Used on a full refund of the most recent purchase: cuts premium
        back to 'now' rather than deleting history. Documented policy: only
        FUTURE access is revoked; time already consumed is not clawed back."""
        user = await self.uow.users.get_by_id(user_id)
        if user is None:
            return
        now = dt.datetime.now(dt.UTC)
        if user.premium_until and user.premium_until > now:
            user.premium_until = now
            await self.uow.flush()
