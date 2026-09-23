"""Integration tests for referral attribution and anti-fraud qualification
(spec section 5 / section 10: "Self-referrals, repeat starts, suspicious
users, and blocked users")."""

from __future__ import annotations

import pytest

from app.services.referral_service import ReferralService


@pytest.mark.asyncio
async def test_normal_referral_is_qualified(uow, make_user):
    referrer = await make_user()
    referred = await make_user()

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer.referral_code
    )

    assert result.created is True
    assert result.referral.is_qualified is True
    assert result.referral.is_self_referral is False
    assert result.referral.is_suspicious is False


@pytest.mark.asyncio
async def test_self_referral_is_rejected(uow, make_user):
    user = await make_user()

    result = await ReferralService(uow).attribute_start(
        new_user=user, referral_code=user.referral_code
    )

    assert result.referral.is_self_referral is True
    assert result.referral.is_qualified is False
    assert result.reason == "self_referral_rejected"


@pytest.mark.asyncio
async def test_repeated_start_before_attribution_is_suspicious_not_qualified(uow, make_user):
    referrer = await make_user()
    referred = await make_user()
    # Simulate the referred user having issued /start more than once BEFORE
    # this attribution call (e.g. bot restart replay, or fraud attempt).
    await uow.users.touch_start(referred)  # start_count becomes 2

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer.referral_code
    )

    assert result.referral.is_qualified is False
    assert result.referral.is_suspicious is True
    assert result.referral.suspicious_reason == "repeated_start_before_attribution"


@pytest.mark.asyncio
async def test_blocked_new_user_is_not_qualified(uow, make_user):
    referrer = await make_user()
    referred = await make_user(is_blocked=True)

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer.referral_code
    )

    assert result.referral.is_qualified is False
    assert result.referral.disqualified_reason == "blocked_account"


@pytest.mark.asyncio
async def test_blocked_referrer_disqualifies_the_join(uow, make_user):
    referrer = await make_user(is_blocked=True)
    referred = await make_user()

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer.referral_code
    )

    assert result.referral.is_qualified is False
    assert result.referral.disqualified_reason == "referrer_blocked"


@pytest.mark.asyncio
async def test_duplicate_attribution_is_idempotent(uow, make_user):
    referrer_a = await make_user()
    referrer_b = await make_user()
    referred = await make_user()

    first = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer_a.referral_code
    )
    # A second, different referral code must NOT re-attribute the user --
    # "one referrer only" (spec section 5).
    second = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code=referrer_b.referral_code
    )

    assert first.created is True
    assert second.created is False
    assert second.reason == "already_attributed"
    assert second.referral.referrer_user_id == first.referral.referrer_user_id


@pytest.mark.asyncio
async def test_unknown_referral_code_does_not_create_a_referral(uow, make_user):
    referred = await make_user()

    result = await ReferralService(uow).attribute_start(
        new_user=referred, referral_code="does-not-exist"
    )

    assert result.created is False
    assert result.reason == "unknown_referral_code"
