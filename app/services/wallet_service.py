"""High-level wallet operations built on top of WalletRepository.apply_ledger_entry.

Every public method here locks the relevant wallet row(s) first (via
`WalletRepository.lock_wallet`) and is safe to call concurrently for the
same user: a second concurrent call will block on the row lock until the
first transaction commits/rolls back, at which point it observes the
already-applied ledger idempotency key (if any) or a freshly consistent
balance.
"""

from __future__ import annotations

from app.db.models.enums import LedgerBalanceBucket, WalletEntryType
from app.db.uow import UnitOfWork


class WalletService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def get_balances(self, user_id: int) -> dict[str, dict[str, int]]:
        wallets = await self.uow.wallets.list_wallets_for_user(user_id)
        return {
            w.currency: {
                "available": w.available_amount,
                "reserved": w.reserved_amount,
                "pending": w.pending_amount,
            }
            for w in wallets
        }

    async def credit_available(
        self,
        *,
        user_id: int,
        currency: str,
        amount: int,
        entry_type: WalletEntryType,
        idempotency_key: str,
        **meta,
    ) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=entry_type,
            bucket=LedgerBalanceBucket.AVAILABLE,
            amount=amount,
            idempotency_key=idempotency_key,
            **meta,
        )

    async def debit_available(
        self,
        *,
        user_id: int,
        currency: str,
        amount: int,
        entry_type: WalletEntryType,
        idempotency_key: str,
        **meta,
    ) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=entry_type,
            bucket=LedgerBalanceBucket.AVAILABLE,
            amount=-amount,
            idempotency_key=idempotency_key,
            **meta,
        )

    async def reserve_from_available(
        self, *, user_id: int, currency: str, amount: int, idempotency_key: str, **meta
    ) -> None:
        """Move `amount` from available -> reserved atomically (two ledger
        rows, same transaction). Raises InsufficientFundsError if the
        available bucket can't cover it; no partial state is left behind
        because both entries are inside the same DB transaction as the
        caller's session and only flushed, not committed, here."""
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_RESERVE,
            bucket=LedgerBalanceBucket.AVAILABLE,
            amount=-amount,
            idempotency_key=f"{idempotency_key}:debit",
            **meta,
        )
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_RESERVE,
            bucket=LedgerBalanceBucket.RESERVED,
            amount=amount,
            idempotency_key=f"{idempotency_key}:credit",
            **meta,
        )

    async def release_reserved_to_available(
        self, *, user_id: int, currency: str, amount: int, idempotency_key: str, **meta
    ) -> None:
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_RELEASE,
            bucket=LedgerBalanceBucket.RESERVED,
            amount=-amount,
            idempotency_key=f"{idempotency_key}:debit_reserved",
            **meta,
        )
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_RELEASE,
            bucket=LedgerBalanceBucket.AVAILABLE,
            amount=amount,
            idempotency_key=f"{idempotency_key}:credit_available",
            **meta,
        )

    async def consume_reserved(
        self, *, user_id: int, currency: str, amount: int, idempotency_key: str, **meta
    ) -> None:
        """Permanently remove `amount` from reserved (e.g. a promo code
        activation actually being used, or a cancelled/expired code's
        unused reserve being written off after release)."""
        if amount <= 0:
            raise ValueError("amount must be > 0")
        wallet = await self.uow.wallets.lock_wallet(user_id, currency)
        await self.uow.wallets.apply_ledger_entry(
            wallet=wallet,
            entry_type=WalletEntryType.PROMO_CODE_FUNDING_CONSUME,
            bucket=LedgerBalanceBucket.RESERVED,
            amount=-amount,
            idempotency_key=idempotency_key,
            **meta,
        )

    async def transaction_history(
        self, user_id: int, currency: str | None = None, limit: int = 50, offset: int = 0
    ):
        return await self.uow.wallets.list_ledger_for_user(
            user_id, currency=currency, limit=limit, offset=offset
        )
