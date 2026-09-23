"""Integration tests: full-premium and discount promo funding math against
a real wallet, insufficient balance rejection, and concurrent redemption
safety (spec section 10)."""

from __future__ import annotations

import asyncio

import pytest

from app.db.models.enums import PromoKind, WalletEntryType
from app.services.promo_service import AttributionRequest, PromoService
from app.services.wallet_service import WalletService


async def _fund_wallet(uow, user_id: int, currency: str, amount: int):
    wallet_service = WalletService(uow)
    await wallet_service.credit_available(
        user_id=user_id,
        currency=currency,
        amount=amount,
        entry_type=WalletEntryType.ADMIN_GIFT,
        idempotency_key=f"fund:{user_id}:{amount}:{currency}",
    )


@pytest.mark.asyncio
async def test_full_premium_code_reserves_exact_worked_example(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)

    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=20,
        attribution=AttributionRequest(kind="none"),
    )

    assert promo.max_uses == 20
    assert promo.total_reserved_amount == 100_000

    wallet = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    assert wallet.available_amount == 0
    assert wallet.reserved_amount == 100_000


@pytest.mark.asyncio
async def test_discount_code_reserves_exact_worked_example(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS", max_discount_percent=50)
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)

    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.PERCENT_DISCOUNT,
        discount_percent=10,
        activations=200,
        attribution=AttributionRequest(kind="none"),
    )

    assert promo.total_reserved_amount == 100_000  # 200 * 500
    assert promo.cost_per_activation == 500

    wallet = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    assert wallet.available_amount == 0
    assert wallet.reserved_amount == 100_000


@pytest.mark.asyncio
async def test_insufficient_balance_rejects_code_creation_without_reserving(
    uow, make_user, make_plan
):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(
        uow, issuer.id, "UZS", 50_000
    )  # not enough for 20 activations (needs 100,000)

    promo_service = PromoService(uow)
    with pytest.raises(ValueError):
        await promo_service.create_user_code(
            issuer_user_id=issuer.id,
            issuer_is_blogger=False,
            plan=plan,
            kind=PromoKind.FULL_PREMIUM,
            discount_percent=0,
            activations=20,
            attribution=AttributionRequest(kind="none"),
        )

    wallet = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    assert wallet.available_amount == 50_000  # untouched
    assert wallet.reserved_amount == 0


@pytest.mark.asyncio
async def test_redeeming_own_code_is_rejected(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=5,
        attribution=AttributionRequest(kind="none"),
    )

    result = await promo_service.redeem(code=promo.code, redeemer_user_id=issuer.id)
    assert result.ok is False
    assert result.reason == "cannot_redeem_own_code"


@pytest.mark.asyncio
async def test_user_cannot_redeem_the_same_code_twice(uow, make_user, make_plan):
    issuer = await make_user()
    redeemer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=5,
        attribution=AttributionRequest(kind="none"),
    )

    first = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)
    second = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)

    assert first.ok is True
    assert second.ok is False
    assert second.reason == "already_redeemed_by_user"


@pytest.mark.asyncio
async def test_concurrent_redemptions_never_exceed_max_uses(
    uow, make_user, make_plan, session_factory
):
    """Fires many redemptions concurrently against a promo with only 3
    activations and asserts AT MOST 3 succeed and remaining_uses never goes
    negative -- the outcome invariant guaranteed by the atomic
    decrement_remaining_use + DB check constraint.

    CAVEAT: this fixture shares a single AsyncSession/SQLite connection
    across the "concurrent" coroutines, so it exercises cooperative
    interleaving under asyncio, not true multi-connection parallelism --
    SQLite also has no real row-level locking. The invariant asserted here
    (never more successes than max_uses, remaining_uses never negative) is
    still meaningful because it is enforced by the atomic
    decrement_remaining_use + DB-level CHECK(remaining_uses >= 0), which is
    the same code path used against real concurrent connections in
    production. Real multi-connection race testing should be run against
    Postgres with separate sessions per task; see README "Testing".
    """
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 15_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=3,
        attribution=AttributionRequest(kind="none"),
    )

    redeemer_ids = [(await make_user()).id for _ in range(8)]
    await uow.session.commit()

    # Each concurrent attempt gets its OWN session/UnitOfWork, matching how
    # separate concurrent HTTP/bot requests would each open their own
    # session in production -- sharing a single AsyncSession across
    # coroutines is not supported by SQLAlchemy and would not exercise a
    # realistic race.
    from app.db.uow import UnitOfWork

    async def try_redeem(redeemer_id: int):
        async with session_factory() as session:
            local_uow = UnitOfWork(session)
            local_promo_service = PromoService(local_uow)
            try:
                result = await local_promo_service.redeem(
                    code=promo.code, redeemer_user_id=redeemer_id
                )
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise

    results = await asyncio.gather(
        *(try_redeem(rid) for rid in redeemer_ids), return_exceptions=True
    )
    successes = [r for r in results if not isinstance(r, Exception) and r.ok]

    assert len(successes) <= 3

    from sqlalchemy import select

    from app.db.models.promo import PromoCode

    refreshed = (
        await uow.session.execute(select(PromoCode).where(PromoCode.id == promo.id))
    ).scalar_one()
    assert refreshed.remaining_uses >= 0
    assert refreshed.remaining_uses == promo.max_uses - len(successes)


@pytest.mark.asyncio
async def test_cancelling_promo_releases_unused_reserve(uow, make_user, make_plan):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=20,
        attribution=AttributionRequest(kind="none"),
    )

    redeemer = await make_user()
    await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)  # consumes 1 of 20

    await promo_service.cancel(promo, reason="issuer requested cancellation")

    wallet = await uow.wallets.get_or_create_wallet(issuer.id, "UZS")
    # 19 unused activations * 5000 = 95,000 released back to available.
    assert wallet.available_amount == 95_000
    assert wallet.reserved_amount == 0


@pytest.mark.asyncio
async def test_external_url_attribution_requires_admin_approval_before_redeemable(
    uow, make_user, make_plan
):
    issuer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    await _fund_wallet(uow, issuer.id, "UZS", 100_000)
    promo_service = PromoService(uow)
    promo = await promo_service.create_user_code(
        issuer_user_id=issuer.id,
        issuer_is_blogger=False,
        plan=plan,
        kind=PromoKind.FULL_PREMIUM,
        discount_percent=0,
        activations=5,
        attribution=AttributionRequest(kind="external_url", value="https://example.com/mychannel"),
    )

    assert promo.moderation_status == "pending"
    assert promo.is_active is False

    redeemer = await make_user()
    result = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)
    assert result.ok is False
    assert result.reason == "not_redeemable"

    # Admin approves -> becomes redeemable.
    await promo_service.moderate(promo, approve=True, admin_id=1)
    result2 = await promo_service.redeem(code=promo.code, redeemer_user_id=redeemer.id)
    assert result2.ok is True
