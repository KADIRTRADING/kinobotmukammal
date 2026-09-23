"""Premium purchase orchestration: order creation, payment confirmation,
referral commission accrual, and refund/reversal handling.

This is the service payment webhooks (app/api/webhooks) and the wallet
checkout handler both call into, so there's exactly one code path that
ever activates premium or pays a referral commission from a purchase.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.db.models.enums import (
    EntitlementSource,
    OrderKind,
    OrderStatus,
    PaymentProviderCode,
    RewardStatus,
)
from app.db.models.order import Order
from app.db.models.plan import PremiumPlan
from app.db.uow import UnitOfWork
from app.services.blogger_reward_service import BloggerRewardService
from app.services.commission import (
    CommissionInput,
    calculate_referral_commission,
    reverse_commission_amount,
)
from app.services.entitlement_service import EntitlementService
from app.services.money import apply_percent_discount
from app.services.settings_service import SettingsService
from app.services.wallet_service import WalletService


@dataclass(frozen=True)
class CheckoutQuote:
    plan: PremiumPlan
    gross_amount: int
    discount_percent: int
    net_amount: int
    currency: str


class PurchaseService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def quote(self, plan: PremiumPlan, *, discount_percent: int = 0) -> CheckoutQuote:
        net = (
            apply_percent_discount(plan.price_amount, discount_percent)
            if discount_percent
            else plan.price_amount
        )
        return CheckoutQuote(
            plan=plan,
            gross_amount=plan.price_amount,
            discount_percent=discount_percent,
            net_amount=net,
            currency=plan.currency,
        )

    async def create_order(
        self,
        *,
        buyer_user_id: int,
        plan: PremiumPlan,
        provider_code: PaymentProviderCode,
        recipient_user_id: int | None = None,
        discount_percent: int = 0,
        promo_code_id: int | None = None,
        kind: OrderKind = OrderKind.PREMIUM_PURCHASE,
    ) -> Order:
        quote = await self.quote(plan, discount_percent=discount_percent)
        order = await self.uow.orders.create(
            buyer_user_id=buyer_user_id,
            recipient_user_id=recipient_user_id,
            kind=kind.value,
            plan_id=plan.id,
            plan_price_snapshot=plan.price_amount,
            currency=plan.currency,
            discount_percent_applied=discount_percent,
            promo_code_id=promo_code_id,
            gross_amount=quote.gross_amount,
            net_amount=quote.net_amount,
            standard_referral_percent_snapshot=plan.standard_referral_percent,
            blogger_referral_percent_snapshot=plan.blogger_referral_percent,
            blogger_acquisition_reward_enabled_snapshot=plan.blogger_acquisition_reward_enabled,
            provider_code=provider_code.value,
            status=OrderStatus.PENDING.value,
        )
        return order

    async def confirm_payment(self, order: Order, *, provider_reference: str | None = None) -> None:
        """Idempotent: safe to call more than once for the same order (e.g.
        duplicate webhook delivery) -- only the first call transitions the
        order and performs side effects."""
        locked = await self.uow.orders.lock(order.id)
        if locked is None or locked.status == OrderStatus.PAID.value:
            return  # already processed -- duplicate webhook, no-op

        await self.uow.orders.mark_paid(locked, provider_reference=provider_reference)

        plan = await self.uow.plans.get(locked.plan_id)
        recipient_id = locked.recipient_user_id or locked.buyer_user_id

        entitlement_service = EntitlementService(self.uow)
        await entitlement_service.grant(
            user_id=recipient_id,
            plan_id=plan.id,
            duration_days=plan.duration_days,
            source=(
                EntitlementSource.PURCHASE
                if locked.kind == OrderKind.PREMIUM_PURCHASE.value
                else EntitlementSource.GIFT
            ),
            source_reference=str(locked.uid),
        )

        await self._accrue_referral_commission(locked, plan)

    async def _accrue_referral_commission(self, order: Order, plan: PremiumPlan) -> None:
        referred_user_id = order.buyer_user_id  # commission is earned on the BUYER's referral chain
        referral = await self.uow.referrals.get_by_referred_user(referred_user_id)
        if referral is None or referral.is_self_referral:
            return

        existing_commission = await self.uow.rewards.get_commission_by_order(order.id)
        if existing_commission is not None:
            return  # already paid for this order -- idempotent

        prior_orders = await self.uow.orders.list_for_user(referred_user_id, limit=1000)
        paid_before_this = [
            o for o in prior_orders if o.status == OrderStatus.PAID.value and o.id != order.id
        ]
        is_first_purchase = len(paid_before_this) == 0

        settings_service = SettingsService(self.uow)
        applies_to_renewals = await settings_service.referral_commission_on_renewals()

        commission_input = CommissionInput(
            net_paid_amount=order.net_amount,
            standard_referral_percent=order.standard_referral_percent_snapshot,
            blogger_referral_percent=order.blogger_referral_percent_snapshot,
            referrer_is_blogger=referral.referrer_was_blogger_at_join,
            is_first_purchase_of_referred_user=is_first_purchase,
            commission_applies_to_renewals=applies_to_renewals,
        )
        result = calculate_referral_commission(commission_input)
        if not result.eligible or result.amount <= 0:
            return

        commission = await self.uow.rewards.create_commission(
            order_id=order.id,
            referral_id=referral.id,
            referrer_user_id=referral.referrer_user_id,
            plan_id=plan.id,
            commission_percent_snapshot=result.percent_used,
            eligible_net_amount_snapshot=order.net_amount,
            was_blogger_rate_snapshot=result.used_blogger_rate,
            amount=result.amount,
            currency=order.currency,
            status=RewardStatus.ACCRUED.value,
            is_first_purchase_of_referred_user=is_first_purchase,
        )

        wallet_service = WalletService(self.uow)
        await wallet_service.credit_available(
            user_id=referral.referrer_user_id,
            currency=order.currency,
            amount=result.amount,
            entry_type="referral_commission",
            idempotency_key=f"referral_commission:{commission.id}",
            reference_type="referral_commission",
            reference_id=str(commission.id),
            note=f"Referral commission for order {order.uid}",
        )

        # A blogger referrer keeps ALL standard rights AND earns the
        # separate per-qualified-join acquisition reward -- that reward is
        # accrued at attribution time (see referral_service +
        # blogger_reward_service), not here, since it is per-JOIN, not
        # per-PURCHASE. This call is a defensive no-op if already accrued.
        reward_service = BloggerRewardService(self.uow)
        await reward_service.accrue_for_qualified_referral(referral)

    async def refund_order(
        self,
        order: Order,
        *,
        reason: str,
        refunded_numerator: int = 1,
        refunded_denominator: int = 1,
    ) -> None:
        """Reverses commission proportionally and revokes future premium
        access. `refunded_numerator/denominator` supports partial refunds;
        default is a full refund (1/1)."""
        locked = await self.uow.orders.lock(order.id)
        if locked is None or locked.status == OrderStatus.REFUNDED.value:
            return
        if locked.status != OrderStatus.PAID.value:
            return  # nothing to refund if it was never paid

        await self.uow.orders.mark_refunded(locked, reason=reason)

        if refunded_numerator == refunded_denominator:
            entitlement_service = EntitlementService(self.uow)
            await entitlement_service.revoke_future(
                locked.recipient_user_id or locked.buyer_user_id
            )

        commission = await self.uow.rewards.get_commission_by_order(locked.id)
        if commission is not None and commission.status == RewardStatus.ACCRUED.value:
            reversal_amount = reverse_commission_amount(
                commission.amount, refunded_numerator, refunded_denominator
            )
            if reversal_amount > 0:
                from app.services.money import InsufficientFundsError

                wallet_service = WalletService(self.uow)
                try:
                    await wallet_service.debit_available(
                        user_id=commission.referrer_user_id,
                        currency=commission.currency,
                        amount=reversal_amount,
                        entry_type="commission_reversal",
                        idempotency_key=f"commission_reversal:{commission.id}",
                        reference_type="referral_commission",
                        reference_id=str(commission.id),
                        note=f"Refund reversal: {reason}",
                    )
                except InsufficientFundsError as exc:
                    # Documented policy: the referrer already spent/withdrew
                    # the commission. We claw back whatever is currently
                    # available and record the shortfall for admin
                    # collection/review rather than pushing the balance
                    # negative or silently dropping the reversal.
                    if exc.available > 0:
                        await wallet_service.debit_available(
                            user_id=commission.referrer_user_id,
                            currency=commission.currency,
                            amount=exc.available,
                            entry_type="commission_reversal",
                            idempotency_key=f"commission_reversal:{commission.id}",
                            reference_type="referral_commission",
                            reference_id=str(commission.id),
                            note=f"Partial refund reversal (shortfall {reversal_amount - exc.available}): {reason}",
                        )
            if refunded_numerator == refunded_denominator:
                commission.status = RewardStatus.REVERSED.value
                commission.reversed_at = dt.datetime.now(dt.UTC)
                commission.reversal_reason = reason
                await self.uow.flush()
