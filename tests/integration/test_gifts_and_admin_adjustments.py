"""Integration tests: gifting premium/balance user-to-user, admin gifts,
and manual admin balance adjustments (spec section 10)."""

from __future__ import annotations

import pytest

from app.db.models.enums import WalletEntryType
from app.services.gift_service import GiftService
from app.services.money import InsufficientFundsError
from app.services.wallet_service import WalletService


async def _fund(uow, user_id, currency, amount):
    await WalletService(uow).credit_available(
        user_id=user_id,
        currency=currency,
        amount=amount,
        entry_type=WalletEntryType.ADMIN_GIFT,
        idempotency_key=f"fund:{user_id}:{amount}:{currency}:{id(object())}",
    )


@pytest.mark.asyncio
async def test_gift_premium_debits_sender_exactly_once_and_grants_entitlement_exactly_once(
    uow, make_user, make_plan
):
    sender = await make_user()
    recipient = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS", duration_days=30)
    await _fund(uow, sender.id, "UZS", 5000)

    gift_service = GiftService(uow)
    gift = await gift_service.gift_premium_from_user(
        sender_user_id=sender.id, recipient_user_id=recipient.id, plan_id=plan.id
    )

    sender_wallet = await uow.wallets.get_or_create_wallet(sender.id, "UZS")
    assert sender_wallet.available_amount == 0

    recipient_user = await uow.users.get_by_id(recipient.id)
    assert recipient_user.premium_until is not None

    entitlements = await uow.orders.list_entitlements_for_user(recipient.id)
    assert len(entitlements) == 1
    assert entitlements[0].source_reference == f"gift:{gift.id}"


@pytest.mark.asyncio
async def test_gift_premium_fails_cleanly_on_insufficient_balance(uow, make_user, make_plan):
    sender = await make_user()
    recipient = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    # sender has no balance at all

    gift_service = GiftService(uow)
    with pytest.raises(InsufficientFundsError):
        await gift_service.gift_premium_from_user(
            sender_user_id=sender.id, recipient_user_id=recipient.id, plan_id=plan.id
        )

    recipient_user = await uow.users.get_by_id(recipient.id)
    assert recipient_user.premium_until is None


@pytest.mark.asyncio
async def test_gift_balance_moves_funds_atomically(uow, make_user):
    sender = await make_user()
    recipient = await make_user()
    await _fund(uow, sender.id, "UZS", 10_000)

    gift_service = GiftService(uow)
    await gift_service.gift_balance_from_user(
        sender_user_id=sender.id, recipient_user_id=recipient.id, currency="UZS", amount=3000
    )

    sender_wallet = await uow.wallets.get_or_create_wallet(sender.id, "UZS")
    recipient_wallet = await uow.wallets.get_or_create_wallet(recipient.id, "UZS")
    assert sender_wallet.available_amount == 7000
    assert recipient_wallet.available_amount == 3000


@pytest.mark.asyncio
async def test_admin_gift_premium_requires_no_sender_balance(uow, make_user, make_plan):
    recipient = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS", duration_days=7)

    gift_service = GiftService(uow)
    await gift_service.admin_gift_premium(
        admin_id=1, recipient_user_id=recipient.id, plan_id=plan.id, reason="loyalty bonus"
    )

    recipient_user = await uow.users.get_by_id(recipient.id)
    assert recipient_user.premium_until is not None


@pytest.mark.asyncio
async def test_admin_gift_balance_credits_ledger_with_reason(uow, make_user):
    recipient = await make_user()
    gift_service = GiftService(uow)
    await gift_service.admin_gift_balance(
        admin_id=1,
        recipient_user_id=recipient.id,
        currency="UZS",
        amount=2000,
        reason="compensation",
    )

    wallet = await uow.wallets.get_or_create_wallet(recipient.id, "UZS")
    assert wallet.available_amount == 2000

    history = await WalletService(uow).transaction_history(recipient.id, currency="UZS")
    assert any(e.note == "compensation" for e in history)


@pytest.mark.asyncio
async def test_manual_admin_balance_adjustment_can_debit_and_never_goes_negative(uow, make_user):
    user = await make_user()
    await _fund(uow, user.id, "UZS", 1000)

    wallet_service = WalletService(uow)
    await wallet_service.debit_available(
        user_id=user.id,
        currency="UZS",
        amount=1000,
        entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
        idempotency_key="adjust:1",
        note="correction",
    )
    wallet = await uow.wallets.get_or_create_wallet(user.id, "UZS")
    assert wallet.available_amount == 0

    with pytest.raises(InsufficientFundsError):
        await wallet_service.debit_available(
            user_id=user.id,
            currency="UZS",
            amount=1,
            entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
            idempotency_key="adjust:2",
            note="overdraft attempt",
        )
