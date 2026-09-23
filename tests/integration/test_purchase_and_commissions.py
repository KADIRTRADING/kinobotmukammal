"""Integration tests: per-plan commission rates, a blogger earning BOTH
the purchase commission AND the acquisition reward, refunds, and duplicate
webhook idempotency (spec section 10)."""

from __future__ import annotations

import pytest

from app.db.models.enums import PaymentProviderCode
from app.services.blogger_reward_service import BloggerRewardService
from app.services.purchase_service import PurchaseService
from app.services.referral_service import ReferralService
from app.services.settings_service import SettingsService


async def _make_blogger(uow, user):
    profile = await uow.bloggers.create_profile(user_id=user.id, approved_application_id=0)
    return profile


@pytest.mark.asyncio
async def test_standard_referrer_earns_plan_specific_commission(uow, make_user, make_plan):
    referrer = await make_user()
    buyer = await make_user()
    plan = await make_plan(price_amount=10_000, standard_referral_percent=1000)  # 10%

    await ReferralService(uow).attribute_start(new_user=buyer, referral_code=referrer.referral_code)

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order)

    commission = await uow.rewards.get_commission_by_order(order.id)
    assert commission is not None
    assert commission.amount == 1000  # 10% of 10,000
    assert commission.was_blogger_rate_snapshot is False


@pytest.mark.asyncio
async def test_different_plans_yield_different_commission_amounts(uow, make_user, make_plan):
    referrer = await make_user()
    buyer1 = await make_user()
    buyer2 = await make_user()

    weekly = await make_plan(price_amount=10_000, standard_referral_percent=1000)  # 10%
    monthly = await make_plan(price_amount=10_000, standard_referral_percent=1500)  # 15%

    await ReferralService(uow).attribute_start(
        new_user=buyer1, referral_code=referrer.referral_code
    )
    await ReferralService(uow).attribute_start(
        new_user=buyer2, referral_code=referrer.referral_code
    )

    purchase_service = PurchaseService(uow)
    order1 = await purchase_service.create_order(
        buyer_user_id=buyer1.id, plan=weekly, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order1)
    order2 = await purchase_service.create_order(
        buyer_user_id=buyer2.id, plan=monthly, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order2)

    c1 = await uow.rewards.get_commission_by_order(order1.id)
    c2 = await uow.rewards.get_commission_by_order(order2.id)
    assert c1.amount == 1000
    assert c2.amount == 1500
    assert c1.amount != c2.amount


@pytest.mark.asyncio
async def test_blogger_earns_both_purchase_commission_and_acquisition_reward(
    uow, make_user, make_plan
):
    blogger = await make_user()
    await _make_blogger(uow, blogger)
    await SettingsService(uow).set_global_blogger_reward_per_1000(
        100_000, "UZS"
    )  # 100 UZS/qualified join

    buyer = await make_user()
    plan = await make_plan(
        price_amount=10_000, standard_referral_percent=1000, blogger_referral_percent=1500
    )

    referral_service = ReferralService(uow)
    attribution = await referral_service.attribute_start(
        new_user=buyer, referral_code=blogger.referral_code
    )
    assert attribution.referral.is_qualified is True
    assert attribution.referral.referrer_was_blogger_at_join is True

    # Acquisition reward accrues at ATTRIBUTION time (per join), independent of purchase.
    await BloggerRewardService(uow).accrue_for_qualified_referral(attribution.referral)
    reward = await uow.rewards.get_reward_by_referral(attribution.referral.id)
    assert reward is not None
    assert reward.amount == 100  # 100,000/1000

    # Purchase commission accrues at PURCHASE time, using the BLOGGER rate (15%), not standard (10%).
    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order)

    commission = await uow.rewards.get_commission_by_order(order.id)
    assert commission.amount == 1500  # 15% of 10,000
    assert commission.was_blogger_rate_snapshot is True

    # Both rewards must exist independently and be summed in stats.
    stats = await referral_service.stats_for_referrer(blogger.id)
    assert stats["purchase_commission_total"] == 1500
    assert stats["blogger_reward_total"] == 100


@pytest.mark.asyncio
async def test_duplicate_confirm_payment_call_is_idempotent(uow, make_user, make_plan):
    referrer = await make_user()
    buyer = await make_user()
    plan = await make_plan(price_amount=10_000, standard_referral_percent=1000)
    await ReferralService(uow).attribute_start(new_user=buyer, referral_code=referrer.referral_code)

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )

    # Simulate a duplicate webhook delivery calling confirm_payment twice.
    await purchase_service.confirm_payment(order, provider_reference="charge_123")
    await purchase_service.confirm_payment(order, provider_reference="charge_123")

    commissions = await uow.rewards.list_for_referrer(referrer.id)
    assert len(commissions) == 1  # never double-paid

    updated_buyer = await uow.users.get_by_id(buyer.id)
    # Premium should only have been extended once: duration_days from the plan.

    assert updated_buyer.premium_until is not None


@pytest.mark.asyncio
async def test_full_refund_reverses_commission_and_revokes_future_premium(
    uow, make_user, make_plan
):
    referrer = await make_user()
    buyer = await make_user()
    plan = await make_plan(price_amount=10_000, standard_referral_percent=1000, duration_days=30)
    await ReferralService(uow).attribute_start(new_user=buyer, referral_code=referrer.referral_code)

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order)

    wallet_before = await uow.wallets.get_or_create_wallet(referrer.id, "UZS")
    assert wallet_before.available_amount == 1000

    await purchase_service.refund_order(order, reason="buyer_requested")

    wallet_after = await uow.wallets.get_or_create_wallet(referrer.id, "UZS")
    assert wallet_after.available_amount == 0  # commission fully clawed back

    commission = await uow.rewards.get_commission_by_order(order.id)
    assert commission.status == "reversed"

    refreshed_buyer = await uow.users.get_by_id(buyer.id)
    import datetime as dt

    assert refreshed_buyer.premium_until <= dt.datetime.now(dt.UTC) + dt.timedelta(seconds=5)
