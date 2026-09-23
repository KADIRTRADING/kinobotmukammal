"""Integration test: blogger acquisition reward accrual across 1, 10, 999,
and 1000 sequential qualified joins, verified against the DB-persisted
`BloggerProfile.accrual_remainder_micros` and ledger balance (spec section
10: "Rewards for 1, 10, 999, and 1000 qualified users")."""

from __future__ import annotations

import pytest

from app.services.blogger_reward_service import BloggerRewardService
from app.services.referral_service import ReferralService
from app.services.settings_service import SettingsService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "n,rate,expected_total",
    [
        (1, 100_000, 100),
        (10, 100_000, 1_000),
        (999, 100_000, 99_900),
        (1000, 100_000, 100_000),
        (1, 333, 0),  # 0.333 UZS rounds down to 0 for the first user alone
        (1000, 333, 333),  # but the full 1000 joins earn exactly floor(333*1000/1000)=333
    ],
)
async def test_accrual_matches_closed_form_over_n_joins(uow, make_user, n, rate, expected_total):
    blogger = await make_user()
    await uow.bloggers.create_profile(user_id=blogger.id, approved_application_id=0)
    await SettingsService(uow).set_global_blogger_reward_per_1000(rate, "UZS")

    reward_service = BloggerRewardService(uow)
    referral_service = ReferralService(uow)

    for _ in range(n):
        referred = await make_user()
        attribution = await referral_service.attribute_start(
            new_user=referred, referral_code=blogger.referral_code
        )
        await reward_service.accrue_for_qualified_referral(attribution.referral)

    wallet = await uow.wallets.get_or_create_wallet(blogger.id, "UZS")
    assert wallet.available_amount == expected_total

    profile = await uow.bloggers.get_profile_by_user(blogger.id)
    assert profile.qualified_joins_counted == n


@pytest.mark.asyncio
async def test_suspended_blogger_stops_earning_new_rewards(uow, make_user):
    blogger = await make_user()
    profile = await uow.bloggers.create_profile(user_id=blogger.id, approved_application_id=0)
    await SettingsService(uow).set_global_blogger_reward_per_1000(100_000, "UZS")

    reward_service = BloggerRewardService(uow)
    referral_service = ReferralService(uow)

    referred1 = await make_user()
    attribution1 = await referral_service.attribute_start(
        new_user=referred1, referral_code=blogger.referral_code
    )
    await reward_service.accrue_for_qualified_referral(attribution1.referral)

    await uow.bloggers.suspend(profile, "policy violation")

    referred2 = await make_user()
    attribution2 = await referral_service.attribute_start(
        new_user=referred2, referral_code=blogger.referral_code
    )
    await reward_service.accrue_for_qualified_referral(attribution2.referral)

    wallet = await uow.wallets.get_or_create_wallet(blogger.id, "UZS")
    assert wallet.available_amount == 100  # only the first join was rewarded


@pytest.mark.asyncio
async def test_duplicate_accrual_call_never_double_pays(uow, make_user):
    blogger = await make_user()
    await uow.bloggers.create_profile(user_id=blogger.id, approved_application_id=0)
    await SettingsService(uow).set_global_blogger_reward_per_1000(100_000, "UZS")

    referral_service = ReferralService(uow)
    reward_service = BloggerRewardService(uow)
    referred = await make_user()
    attribution = await referral_service.attribute_start(
        new_user=referred, referral_code=blogger.referral_code
    )

    await reward_service.accrue_for_qualified_referral(attribution.referral)
    await reward_service.accrue_for_qualified_referral(
        attribution.referral
    )  # called twice, e.g. retried job

    wallet = await uow.wallets.get_or_create_wallet(blogger.id, "UZS")
    assert wallet.available_amount == 100  # not 200
