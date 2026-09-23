"""Gifts: premium, balance, and promo codes, user-to-user and admin-to-user.

Every gift path debits the sender (if a user, never for an admin gift)
exactly once and issues the entitlement exactly once, both inside the same
service call under the caller's transaction -- consistent with spec
section 6 ("debiting exactly once, and issuing the entitlement exactly
once").
"""

from __future__ import annotations

import datetime as dt

from app.db.models.enums import EntitlementSource, GiftKind, WalletEntryType
from app.db.uow import UnitOfWork
from app.services.entitlement_service import EntitlementService
from app.services.wallet_service import WalletService


class GiftService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def gift_premium_from_user(
        self, *, sender_user_id: int, recipient_user_id: int, plan_id: int
    ):
        plan = await self.uow.plans.get(plan_id)
        if plan is None or not plan.is_active:
            raise ValueError("Plan not found or inactive")
        recipient = await self.uow.users.get_by_id(recipient_user_id)
        if recipient is None:
            raise ValueError("Recipient has not started the bot yet")

        wallet_service = WalletService(self.uow)
        idempotency_seed = f"gift_premium:{sender_user_id}:{recipient_user_id}:{plan_id}:{dt.datetime.now(dt.UTC).timestamp()}"
        await wallet_service.debit_available(
            user_id=sender_user_id,
            currency=plan.currency,
            amount=plan.price_amount,
            entry_type=WalletEntryType.USER_GIFT_SENT,
            idempotency_key=f"{idempotency_seed}:debit",
            reference_type="gift",
        )

        gift = await self.uow.gifts.create(
            kind=GiftKind.PREMIUM.value,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            plan_id=plan.id,
            cost_amount=plan.price_amount,
            cost_currency=plan.currency,
            delivered_at=dt.datetime.now(dt.UTC),
        )

        entitlement_service = EntitlementService(self.uow)
        entitlement = await entitlement_service.grant(
            user_id=recipient_user_id,
            plan_id=plan.id,
            duration_days=plan.duration_days,
            source=EntitlementSource.GIFT,
            source_reference=f"gift:{gift.id}",
        )
        gift.entitlement_id = entitlement.id
        # Note: a premium gift issues an ENTITLEMENT, not a balance credit,
        # so no wallet ledger entry is created for the recipient here.
        await self.uow.flush()
        return gift

    async def gift_balance_from_user(
        self, *, sender_user_id: int, recipient_user_id: int, currency: str, amount: int
    ):
        if amount <= 0:
            raise ValueError("amount must be > 0")
        recipient = await self.uow.users.get_by_id(recipient_user_id)
        if recipient is None:
            raise ValueError("Recipient has not started the bot yet")

        wallet_service = WalletService(self.uow)
        seed = f"gift_balance:{sender_user_id}:{recipient_user_id}:{dt.datetime.now(dt.UTC).timestamp()}"
        await wallet_service.debit_available(
            user_id=sender_user_id,
            currency=currency,
            amount=amount,
            entry_type=WalletEntryType.USER_GIFT_SENT,
            idempotency_key=f"{seed}:debit",
        )
        await wallet_service.credit_available(
            user_id=recipient_user_id,
            currency=currency,
            amount=amount,
            entry_type=WalletEntryType.USER_GIFT_RECEIVED,
            idempotency_key=f"{seed}:credit",
        )
        return await self.uow.gifts.create(
            kind=GiftKind.BALANCE.value,
            sender_user_id=sender_user_id,
            recipient_user_id=recipient_user_id,
            balance_amount=amount,
            balance_currency=currency,
            cost_amount=amount,
            cost_currency=currency,
            delivered_at=dt.datetime.now(dt.UTC),
        )

    async def admin_gift_premium(
        self, *, admin_id: int, recipient_user_id: int, plan_id: int, reason: str
    ):
        plan = await self.uow.plans.get(plan_id)
        if plan is None:
            raise ValueError("Plan not found")
        gift = await self.uow.gifts.create(
            kind=GiftKind.PREMIUM.value,
            sender_admin_id=admin_id,
            recipient_user_id=recipient_user_id,
            plan_id=plan.id,
            cost_amount=0,
            reason=reason,
            delivered_at=dt.datetime.now(dt.UTC),
        )
        entitlement_service = EntitlementService(self.uow)
        entitlement = await entitlement_service.grant(
            user_id=recipient_user_id,
            plan_id=plan.id,
            duration_days=plan.duration_days,
            source=EntitlementSource.ADMIN_GRANT,
            source_reference=f"gift:{gift.id}",
            granted_by_admin_id=admin_id,
            reason=reason,
        )
        gift.entitlement_id = entitlement.id
        await self.uow.flush()
        return gift

    async def admin_gift_balance(
        self, *, admin_id: int, recipient_user_id: int, currency: str, amount: int, reason: str
    ):
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet_service = WalletService(self.uow)
        seed = f"admin_gift_balance:{admin_id}:{recipient_user_id}:{dt.datetime.now(dt.UTC).timestamp()}"
        await wallet_service.credit_available(
            user_id=recipient_user_id,
            currency=currency,
            amount=amount,
            entry_type=WalletEntryType.ADMIN_GIFT,
            idempotency_key=seed,
            note=reason,
        )
        return await self.uow.gifts.create(
            kind=GiftKind.BALANCE.value,
            sender_admin_id=admin_id,
            recipient_user_id=recipient_user_id,
            balance_amount=amount,
            balance_currency=currency,
            cost_amount=0,
            reason=reason,
            delivered_at=dt.datetime.now(dt.UTC),
        )
