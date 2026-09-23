"""Integration tests: ledger idempotency-key deduplication (the mechanism
that makes duplicate payment webhooks safe at the wallet layer) and that
wallet balances never go negative under a locked debit (spec section 9/10)."""

from __future__ import annotations

import pytest

from app.db.models.enums import WalletEntryType
from app.services.money import InsufficientFundsError
from app.services.wallet_service import WalletService


@pytest.mark.asyncio
async def test_same_idempotency_key_applied_twice_only_credits_once(uow, make_user):
    user = await make_user()
    wallet_service = WalletService(uow)

    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=500,
        entry_type=WalletEntryType.REFERRAL_COMMISSION,
        idempotency_key="commission:order-42",
    )
    # Simulates a retried/duplicate webhook re-delivering the same event.
    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=500,
        entry_type=WalletEntryType.REFERRAL_COMMISSION,
        idempotency_key="commission:order-42",
    )

    wallet = await uow.wallets.get_or_create_wallet(user.id, "UZS")
    assert wallet.available_amount == 500  # not 1000


@pytest.mark.asyncio
async def test_debit_beyond_available_raises_and_leaves_balance_unchanged(uow, make_user):
    user = await make_user()
    wallet_service = WalletService(uow)
    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=100,
        entry_type=WalletEntryType.ADMIN_GIFT,
        idempotency_key="fund:1",
    )

    with pytest.raises(InsufficientFundsError) as exc_info:
        await wallet_service.debit_available(
            user_id=user.id,
            currency="UZS",
            amount=200,
            entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
            idempotency_key="debit:1",
        )
    assert exc_info.value.available == 100
    assert exc_info.value.requested == 200

    wallet = await uow.wallets.get_or_create_wallet(user.id, "UZS")
    assert wallet.available_amount == 100  # untouched by the failed attempt


@pytest.mark.asyncio
async def test_ledger_entries_sum_matches_cached_wallet_balance(uow, make_user):
    """This is exactly the invariant `app.workers.reconciliation_worker`
    checks continuously in production."""
    user = await make_user()
    wallet_service = WalletService(uow)
    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=1000,
        entry_type=WalletEntryType.ADMIN_GIFT,
        idempotency_key="a",
    )
    await wallet_service.debit_available(
        user_id=user.id,
        currency="UZS",
        amount=300,
        entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
        idempotency_key="b",
    )
    await wallet_service.credit_available(
        user_id=user.id,
        currency="UZS",
        amount=50,
        entry_type=WalletEntryType.REFERRAL_COMMISSION,
        idempotency_key="c",
    )

    wallet = await uow.wallets.get_or_create_wallet(user.id, "UZS")
    entries = await uow.wallets.list_ledger_for_user(user.id, currency="UZS", limit=100)
    available_entries_sum = sum(e.amount for e in entries if e.bucket == "available")

    assert wallet.available_amount == 750
    assert available_entries_sum == wallet.available_amount
