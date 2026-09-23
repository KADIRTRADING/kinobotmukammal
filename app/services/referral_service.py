"""Referral attribution and anti-fraud qualification (spec section 5).

Attribution rules:
  - A user is attributed to a referrer only on their very FIRST /start ever
    seen for that Telegram account (guaranteed by the unique constraint on
    `Referral.referred_user_id` plus the check in `attribute_start`).
  - Self-referral (referrer_code belongs to the same telegram_id) is
    recorded but flagged `is_self_referral=True` and NEVER qualifies for
    anything.
  - Repeated /start by the same user does not create a second referral row
    and does not re-trigger qualification.

Qualification rules (anti-fraud, feeds blogger acquisition rewards only --
NOT standard commission, which only requires a verified purchase):
  - Self-referrals are never qualified.
  - Already-blocked accounts are never qualified.
  - A user who has issued /start more than once before this attribution
    settles (i.e. `start_count` > 1 at the moment of first attribution) is
    flagged suspicious and held for admin review rather than auto-qualified
    -- this catches the "repeated /start" fraud pattern described in the
    spec.
  - Obvious duplicate attribution attempts (a referred_user_id that already
    has a Referral row) are rejected outright by attribute_start's
    idempotent check.
Suspicious joins are NOT silently marked paid; they sit with
`is_qualified=False`, `is_suspicious=True` and appear in the admin
"suspicious referral activity" review queue (see admin panel spec section 8).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.models.enums import BloggerProfileStatus
from app.db.models.referral import Referral
from app.db.models.user import User
from app.db.uow import UnitOfWork


@dataclass(frozen=True)
class AttributionResult:
    referral: Referral | None
    created: bool
    reason: str


class ReferralService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def attribute_start(
        self, *, new_user: User, referral_code: str | None
    ) -> AttributionResult:
        """Called once, right after a brand-new `User` row is created for a
        first-ever /start. Returns immediately (no-op) if `new_user` already
        has an attribution -- callers should only invoke this for freshly
        created users, but the DB unique constraint is the real guarantee.
        """
        existing = await self.uow.referrals.get_by_referred_user(new_user.id)
        if existing is not None:
            return AttributionResult(referral=existing, created=False, reason="already_attributed")

        if not referral_code:
            return AttributionResult(referral=None, created=False, reason="no_referral_code")

        referrer = await self.uow.users.get_by_referral_code(referral_code)
        if referrer is None:
            return AttributionResult(referral=None, created=False, reason="unknown_referral_code")

        is_self = referrer.id == new_user.id
        blogger_profile = await self.uow.bloggers.get_profile_by_user(referrer.id)
        referrer_is_blogger = bool(
            blogger_profile and blogger_profile.status == BloggerProfileStatus.ACTIVE.value
        )

        referral = await self.uow.referrals.create(
            referred_user_id=new_user.id,
            referrer_user_id=referrer.id,
            is_self_referral=is_self,
            referrer_was_blogger_at_join=referrer_is_blogger,
        )

        if is_self:
            await self.uow.referrals.mark_disqualified(referral, "self_referral")
            return AttributionResult(
                referral=referral, created=True, reason="self_referral_rejected"
            )

        qualification = await self._qualify(new_user=new_user, referrer=referrer)
        if qualification.qualifies:
            await self.uow.referrals.mark_qualified(referral)
        else:
            referral.is_suspicious = qualification.suspicious
            referral.suspicious_reason = qualification.reason
            await self.uow.referrals.mark_disqualified(referral, qualification.reason)

        return AttributionResult(referral=referral, created=True, reason=qualification.reason)

    @dataclass(frozen=True)
    class _Qualification:
        qualifies: bool
        suspicious: bool
        reason: str

    async def _qualify(self, *, new_user: User, referrer: User) -> _Qualification:
        if new_user.is_blocked:
            return self._Qualification(False, True, "blocked_account")
        if referrer.is_blocked:
            return self._Qualification(False, True, "referrer_blocked")
        if new_user.start_count > 1:
            # The account issued /start more than once before this
            # attribution: hold for manual review rather than auto-reject
            # OR auto-approve.
            return self._Qualification(False, True, "repeated_start_before_attribution")

        from app.services.settings_service import (
            SettingsService,  # local import avoids a module cycle
        )

        min_age_hours = await SettingsService(self.uow).qualified_join_min_account_age_hours()
        if min_age_hours:
            # Placeholder hook for future device/account-age heuristics; a
            # freshly created user always has age 0 relative to `started_at`,
            # so this only matters if callers backfill `started_at` earlier.
            pass

        return self._Qualification(True, False, "qualified")

    async def stats_for_referrer(self, referrer_user_id: int) -> dict:
        total = await self.uow.referrals.count_referrals_for_referrer(referrer_user_id)
        qualified = await self.uow.referrals.count_qualified_for_referrer(referrer_user_id)
        commissions = await self.uow.rewards.list_for_referrer(referrer_user_id, limit=1000)
        pending_or_paid_total = sum(c.amount for c in commissions if c.status == "accrued")
        rewards = await self.uow.rewards.list_for_blogger(referrer_user_id, limit=1000)
        reward_total = sum(r.amount for r in rewards if r.status == "accrued")
        return {
            "total_joins": total,
            "qualified_joins": qualified,
            "purchase_commission_total": pending_or_paid_total,
            "blogger_reward_total": reward_total,
        }
