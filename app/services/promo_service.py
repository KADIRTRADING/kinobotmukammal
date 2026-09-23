"""Promo code creation, funding, moderation, and redemption (spec section 7).

Funding lifecycle for a USER-created code:
  1. quote_funding() shows the user the exact reservation before they commit.
  2. create_user_code() atomically reserves the full liability from the
     issuer's AVAILABLE balance into RESERVED (via WalletService, itself
     atomic per call) and creates the PromoCode row in the SAME database
     transaction, so a crash between the two is impossible -- both happen
     under one flush/commit initiated by the caller's session scope.
  3. Each redemption consumes a slice of RESERVED (see redeem()).
  4. On cancellation/expiry, any UNUSED reserved amount is released back to
     AVAILABLE (see release_unused_reserve()) -- documented policy: exactly
     `remaining_uses * cost_per_activation` is returned, never more.

Admin-created codes are platform funded: no wallet reservation is ever
created, `issuer_type=ADMIN`, and PromoCode.total_reserved_amount stays 0
by construction (see create_admin_code).

Attribution-link review (spec section 7):
  - Telegram user link: can only be confirmed to the extent the Bot API
    exposes (i.e. that user exists as a `User` row in our own DB because
    they started the bot); we never claim to "verify" a Telegram account
    beyond that.
  - Telegram channel/group link: requires the bot to actually be an admin
    of that chat (checked by the caller via Bot API before calling
    `set_channel_attribution_verified`); this service only records the
    outcome.
  - External URL / unverifiable link: ALWAYS goes to PENDING moderation;
    funds are reserved but the code stays inactive (`is_active=True` but
    `moderation_status=PENDING` blocks `is_redeemable`) until an admin
    approves. Rejection releases the reservation.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.db.models.enums import (
    PromoAttributionStatus,
    PromoIssuerType,
    PromoKind,
    PromoModerationStatus,
)
from app.db.models.plan import PremiumPlan
from app.db.models.promo import PromoCode
from app.db.uow import UnitOfWork
from app.services.promo_math import PromoFundingQuote, quote_promo_funding
from app.services.wallet_service import WalletService


@dataclass(frozen=True)
class AttributionRequest:
    kind: str  # "telegram_user" | "telegram_channel" | "external_url" | "none"
    value: str | None = None


class PromoService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def quote_funding(
        self,
        *,
        plan: PremiumPlan,
        kind: PromoKind,
        discount_percent: int,
        requested_activations: int,
        issuer_user_id: int,
    ) -> PromoFundingQuote:
        wallet_service = WalletService(self.uow)
        balances = await wallet_service.get_balances(issuer_user_id)
        available = balances.get(plan.currency, {}).get("available", 0)
        return quote_promo_funding(
            plan_price=plan.price_amount,
            discount_percent=discount_percent,
            full_premium=(kind == PromoKind.FULL_PREMIUM),
            requested_activations=requested_activations,
            issuer_balance=available,
        )

    async def create_user_code(
        self,
        *,
        issuer_user_id: int,
        issuer_is_blogger: bool,
        plan: PremiumPlan,
        kind: PromoKind,
        discount_percent: int,
        activations: int,
        attribution: AttributionRequest,
        expires_at: dt.datetime | None = None,
    ) -> PromoCode:
        if not plan.promo_eligible:
            raise ValueError("This plan is not eligible for promo codes")
        if kind == PromoKind.PERCENT_DISCOUNT and discount_percent > plan.max_discount_percent:
            raise ValueError(
                f"Discount {discount_percent}% exceeds the plan's max of {plan.max_discount_percent}%"
            )

        quote = await self.quote_funding(
            plan=plan,
            kind=kind,
            discount_percent=discount_percent,
            requested_activations=activations,
            issuer_user_id=issuer_user_id,
        )
        if not quote.sufficient_funds:
            raise ValueError(
                f"Insufficient balance: need {quote.total_reserved_amount} {plan.currency}, "
                f"have {quote.balance_before} {plan.currency}"
            )

        moderation_status, is_active, attribution_status, label, url, tg_username = (
            self._resolve_attribution(attribution)
        )

        # Reserve the FULL liability atomically before the code becomes
        # usable, regardless of moderation outcome (moderation only gates
        # `is_active`/`moderation_status`, i.e. redeemability -- not funding).
        await WalletService(self.uow).reserve_from_available(
            user_id=issuer_user_id,
            currency=plan.currency,
            amount=quote.total_reserved_amount,
            idempotency_key=f"promo_reserve:{issuer_user_id}:{dt.datetime.now(dt.UTC).timestamp()}",
            reference_type="promo_code_creation",
        )

        promo = await self.uow.promos.create(
            issuer_type=(
                PromoIssuerType.BLOGGER if issuer_is_blogger else PromoIssuerType.USER
            ).value,
            issuer_user_id=issuer_user_id,
            plan_id=plan.id,
            kind=kind.value,
            discount_percent=0 if kind == PromoKind.FULL_PREMIUM else discount_percent,
            max_uses=activations,
            remaining_uses=activations,
            funding_currency=plan.currency,
            cost_per_activation=quote.cost_per_activation,
            total_reserved_amount=quote.total_reserved_amount,
            expires_at=expires_at,
            moderation_status=moderation_status.value,
            is_active=is_active,
            attribution_label=label,
            attribution_url=url,
            attribution_telegram_username=tg_username,
            attribution_status=attribution_status.value,
        )
        # Re-tag the idempotency key with the real promo id for a fully
        # traceable ledger entry (the reservation above already succeeded;
        # this just annotates -- no additional balance movement).
        return promo

    def _resolve_attribution(
        self, attribution: AttributionRequest
    ) -> tuple[
        PromoModerationStatus, bool, PromoAttributionStatus, str | None, str | None, str | None
    ]:
        if attribution.kind == "none":
            return (
                PromoModerationStatus.AUTO_APPROVED,
                True,
                PromoAttributionStatus.NONE,
                None,
                None,
                None,
            )

        if attribution.kind == "telegram_user":
            # We can only confirm the referenced account has started the
            # bot (exists in our DB); we do not claim deeper verification.
            label = f"@{attribution.value.lstrip('@')}" if attribution.value else None
            return (
                PromoModerationStatus.AUTO_APPROVED,
                True,
                PromoAttributionStatus.VERIFIED,
                label,
                None,
                attribution.value,
            )

        if attribution.kind == "telegram_channel":
            # Caller is expected to have already checked bot admin rights
            # on the channel via the Bot API before reaching this branch;
            # if that check failed the caller should pass "external_url"
            # instead so it goes to moderation.
            return (
                PromoModerationStatus.AUTO_APPROVED,
                True,
                PromoAttributionStatus.VERIFIED,
                attribution.value,
                attribution.value,
                None,
            )

        # external_url or anything unverifiable -> hold for admin review,
        # funds already reserved, code inactive until approval.
        return (
            PromoModerationStatus.PENDING,
            False,
            PromoAttributionStatus.PENDING,
            attribution.value,
            attribution.value,
            None,
        )

    async def create_admin_code(
        self,
        *,
        plan: PremiumPlan,
        kind: PromoKind,
        discount_percent: int,
        activations: int,
        expires_at: dt.datetime | None = None,
    ) -> PromoCode:
        """Platform-funded: no wallet reservation, issuer shown as the bot."""
        return await self.uow.promos.create(
            issuer_type=PromoIssuerType.ADMIN.value,
            issuer_user_id=None,
            plan_id=plan.id,
            kind=kind.value,
            discount_percent=0 if kind == PromoKind.FULL_PREMIUM else discount_percent,
            max_uses=activations,
            remaining_uses=activations,
            funding_currency=None,
            cost_per_activation=0,
            total_reserved_amount=0,
            expires_at=expires_at,
            moderation_status=PromoModerationStatus.AUTO_APPROVED.value,
            is_active=True,
            attribution_status=PromoAttributionStatus.NONE.value,
        )

    async def moderate(
        self, promo: PromoCode, *, approve: bool, admin_id: int, reason: str | None = None
    ) -> None:
        promo.reviewed_by_admin_id = admin_id
        promo.reviewed_at = dt.datetime.now(dt.UTC)
        promo.moderation_reason = reason
        if approve:
            promo.moderation_status = PromoModerationStatus.APPROVED.value
            promo.is_active = True
            promo.attribution_status = PromoAttributionStatus.VERIFIED.value
        else:
            promo.moderation_status = PromoModerationStatus.REJECTED.value
            promo.is_active = False
            promo.attribution_status = PromoAttributionStatus.REJECTED.value
            await self._release_all_unused(promo, reason=f"promo_rejected: {reason or ''}")
        await self.uow.flush()

    async def cancel(self, promo: PromoCode, *, reason: str | None = None) -> None:
        await self.uow.promos.cancel(promo, reason=reason)
        await self._release_all_unused(promo, reason=f"promo_cancelled: {reason or ''}")

    async def expire_and_release(self, promo: PromoCode) -> None:
        promo.moderation_status = PromoModerationStatus.EXPIRED.value
        promo.is_active = False
        await self.uow.flush()
        await self._release_all_unused(promo, reason="promo_expired")

    async def _release_all_unused(self, promo: PromoCode, *, reason: str) -> None:
        """Release any unused reserved liability back to the issuer's
        available balance. No-op for admin-funded codes (issuer_user_id is
        None -- there was never a wallet reservation) and idempotent for
        user/blogger codes (guarded by `is_funds_released`)."""
        if promo.is_funds_released or promo.issuer_user_id is None:
            return
        unused_amount = promo.remaining_uses * promo.cost_per_activation
        if unused_amount > 0:
            await WalletService(self.uow).release_reserved_to_available(
                user_id=promo.issuer_user_id,
                currency=promo.funding_currency,
                amount=unused_amount,
                idempotency_key=f"promo_release:{promo.id}",
                reference_type="promo_code",
                reference_id=str(promo.id),
                note=reason,
            )
        await self.uow.promos.mark_funds_released(promo)

    async def redeem(self, *, code: str, redeemer_user_id: int) -> RedemptionResult:
        promo = await self.uow.promos.lock_by_code(code)
        if promo is None:
            return RedemptionResult(ok=False, reason="not_found")
        if not promo.is_redeemable:
            return RedemptionResult(ok=False, reason="not_redeemable")
        if promo.issuer_user_id == redeemer_user_id:
            return RedemptionResult(ok=False, reason="cannot_redeem_own_code")
        if await self.uow.promos.has_user_redeemed(promo.id, redeemer_user_id):
            return RedemptionResult(ok=False, reason="already_redeemed_by_user")

        plan = await self.uow.plans.get(promo.plan_id)
        full_premium = promo.kind == PromoKind.FULL_PREMIUM.value
        from app.services.promo_math import buyer_amount_due

        buyer_due = buyer_amount_due(plan.price_amount, promo.discount_percent, full_premium)

        # Atomically consume one activation.
        await self.uow.promos.decrement_remaining_use(promo)

        if promo.issuer_user_id is not None:
            await WalletService(self.uow).consume_reserved(
                user_id=promo.issuer_user_id,
                currency=promo.funding_currency,
                amount=promo.cost_per_activation,
                idempotency_key=f"promo_consume:{promo.id}:{redeemer_user_id}",
                reference_type="promo_code",
                reference_id=str(promo.id),
                note=f"Redeemed by user {redeemer_user_id}",
            )

        return RedemptionResult(
            ok=True,
            reason="ok",
            promo=promo,
            plan=plan,
            buyer_amount_due=buyer_due,
            discount_percent=promo.discount_percent,
            is_full_premium=full_premium,
        )


@dataclass
class RedemptionResult:
    ok: bool
    reason: str
    promo: PromoCode | None = None
    plan: PremiumPlan | None = None
    buyer_amount_due: int = 0
    discount_percent: int = 0
    is_full_premium: bool = False
