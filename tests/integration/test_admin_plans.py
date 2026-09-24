"""Integration tests: admin panel "Premium plans" CRUD (spec section on
per-plan durations/prices/referral economics), exercised via
`PlanRepository` -- the same repository `app/bot/handlers/admin/plans.py`
calls for create/edit/toggle."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_plan_with_distinct_referral_rates(uow):
    plan = await uow.plans.create(
        code="weekly",
        title_uz="Haftalik",
        title_ru="Nedelnyi",
        title_en="Weekly",
        duration_days=7,
        price_amount=15_000,
        currency="UZS",
        standard_referral_percent=800,
        blogger_referral_percent=1200,
        blogger_acquisition_reward_enabled=True,
        max_discount_percent=30,
    )
    assert plan.standard_referral_percent == 800
    assert plan.blogger_referral_percent == 1200
    assert plan.is_active is True


@pytest.mark.asyncio
async def test_toggle_plan_active_flag(uow, make_plan):
    plan = await make_plan()
    await uow.plans.update(plan, is_active=False)
    refreshed = await uow.plans.get(plan.id)
    assert refreshed.is_active is False

    await uow.plans.update(refreshed, is_active=True)
    reactivated = await uow.plans.get(plan.id)
    assert reactivated.is_active is True


@pytest.mark.asyncio
async def test_edit_price_and_referral_percent_fields_independently(uow, make_plan):
    plan = await make_plan(price_amount=5000, standard_referral_percent=1000)

    await uow.plans.update(plan, price_amount=7500)
    refreshed = await uow.plans.get(plan.id)
    assert refreshed.price_amount == 7500
    assert refreshed.standard_referral_percent == 1000  # untouched by the price-only edit

    await uow.plans.update(refreshed, blogger_referral_percent=2000)
    refreshed2 = await uow.plans.get(plan.id)
    assert refreshed2.blogger_referral_percent == 2000
    assert refreshed2.price_amount == 7500  # untouched by the referral-only edit


@pytest.mark.asyncio
async def test_plan_code_uniqueness_lookup_used_by_admin_creation_fsm(uow, make_plan):
    await make_plan(code="uniqcode")
    existing = await uow.plans.get_by_code("uniqcode")
    assert existing is not None
    missing = await uow.plans.get_by_code("does-not-exist")
    assert missing is None


@pytest.mark.asyncio
async def test_list_all_plans_includes_inactive_ones_for_admin_view(uow, make_plan):
    active_plan = await make_plan(code="active1")
    inactive_plan = await make_plan(code="inactive1")
    await uow.plans.update(inactive_plan, is_active=False)

    all_plans = await uow.plans.list_all()
    ids = {p.id for p in all_plans}
    assert active_plan.id in ids
    assert inactive_plan.id in ids

    active_only = await uow.plans.list_active()
    active_ids = {p.id for p in active_only}
    assert active_plan.id in active_ids
    assert inactive_plan.id not in active_ids
