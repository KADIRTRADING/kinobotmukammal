"""Integration tests: admin panel "Promo codes" section -- platform-funded
admin-created codes (never reserve issuer wallet funds), the pending
moderation queue used by `ac:pending`/`apr:pending`, and cancelling an
admin-issued code (which is a no-op release since there was never a
wallet reservation to begin with) via `PromoService`/`PromoRepository`,
the same services `app/bot/handlers/admin/promos.py` calls."""

from __future__ import annotations

import pytest

from app.db.models.enums import PromoKind
from app.services.promo_service import PromoService
from app.services.wallet_service import WalletService


@pytest.mark.asyncio
async def test_admin_created_code_is_platform_funded_with_no_wallet_reservation(uow, make_plan):
    plan = await make_plan(price_amount=5000, currency="UZS")
    promo_service = PromoService(uow)

    promo = await promo_service.create_admin_code(
        plan=plan, kind=PromoKind.FULL_PREMIUM, discount_percent=0, activations=10
    )

    assert promo.issuer_user_id is None
    assert promo.total_reserved_amount == 0
    assert promo.cost_per_activation == 0
    assert promo.is_active is True
    assert promo.moderation_status == "auto_approved"


@pytest.mark.asyncio
async def test_admin_code_is_immediately_redeemable_without_moderation(uow, make_user, make_plan):
    plan = await make_plan(price_amount=5000, currency="UZS")
    promo_service = PromoService(uow)
    promo = await promo_service.create_admin_code(
        plan=plan, kind=PromoKind.PERCENT_DISCOUNT, discount_percent=25, activations=5
    )

    redeemer = await make_user()
    result = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)
    assert result.ok is True
    assert result.discount_percent == 25


@pytest.mark.asyncio
async def test_cancelling_admin_code_is_a_safe_no_op_release(uow, make_plan):
    plan = await make_plan(price_amount=5000, currency="UZS")
    promo_service = PromoService(uow)
    promo = await promo_service.create_admin_code(
        plan=plan, kind=PromoKind.FULL_PREMIUM, discount_percent=0, activations=10
    )

    # Must not raise even though there is no issuer wallet to release funds
    # back to (issuer_user_id is None for admin-funded codes).
    await promo_service.cancel(promo, reason="admin decided to retire this code")

    refreshed = await uow.promos.get(promo.id)
    assert refreshed.is_active is False
    assert refreshed.is_funds_released is True


@pytest.mark.asyncio
async def test_pending_moderation_queue_lists_only_pending_user_codes(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await WalletService(uow).credit_available(
        user_id=issuer.id,
        currency="UZS",
        amount=100_000,
        entry_type="admin_gift",
        idempotency_key=f"fund:{issuer.id}",
    )

    from app.services.promo_service import AttributionRequest

    promo_service = PromoService(uow)
    pending_promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=5,
        attribution=AttributionRequest(kind="external_url", value="https://example.com/x"),
    )
    auto_approved_promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=5,
        attribution=AttributionRequest(kind="none"),
    )

    pending_ids = {p.id for p in await uow.promos.list_pending_moderation()}
    assert pending_promo.id in pending_ids
    assert auto_approved_promo.id not in pending_ids

    count = await uow.promos.count_pending_moderation()
    assert count >= 1


@pytest.mark.asyncio
async def test_admin_reject_of_pending_code_releases_issuer_reserve(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await WalletService(uow).credit_available(
        user_id=issuer.id,
        currency="UZS",
        amount=100_000,
        entry_type="admin_gift",
        idempotency_key=f"fund2:{issuer.id}",
    )

    from app.services.promo_service import AttributionRequest

    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=20,
        attribution=AttributionRequest(kind="external_url", value="https://example.com/y"),
    )
    wallet_before = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    assert wallet_before.reserved_amount == 100_000

    await promo_service.moderate(
        promo, approve=False, admin_id=1234, reason="link not owned by issuer"
    )

    wallet_after = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    assert wallet_after.reserved_amount == 0
    assert wallet_after.available_amount == 100_000

    refreshed = await uow.promos.get(promo.id)
    assert refreshed.moderation_status == "rejected"
    assert refreshed.is_active is False
