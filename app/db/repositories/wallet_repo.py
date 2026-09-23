from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import Currency, LedgerBalanceBucket, WalletEntryType
from app.db.models.wallet import LedgerEntry, Wallet


class WalletRepository:
    """All balance mutation goes through `apply_ledger_entry`, which is the
    single choke point that (a) locks the wallet row, (b) checks for
    sufficient funds when debiting, (c) writes the immutable ledger row, and
    (d) updates the cached wallet counters -- all inside the caller's
    existing transaction. This is what makes negative balances and
    lost/duplicate updates structurally impossible under concurrency.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_wallet(self, user_id: int, currency: Currency | str) -> Wallet:
        currency_value = currency.value if isinstance(currency, Currency) else currency
        result = await self.session.execute(
            select(Wallet).where(Wallet.user_id == user_id, Wallet.currency == currency_value)
        )
        wallet = result.scalar_one_or_none()
        if wallet is None:
            wallet = Wallet(user_id=user_id, currency=currency_value)
            self.session.add(wallet)
            await self.session.flush()
        return wallet

    async def lock_wallet(self, user_id: int, currency: Currency | str) -> Wallet:
        """SELECT ... FOR UPDATE on the wallet row. Must be called within an
        open transaction (the async session context manager)."""
        currency_value = currency.value if isinstance(currency, Currency) else currency
        stmt = (
            select(Wallet)
            .where(Wallet.user_id == user_id, Wallet.currency == currency_value)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        wallet = result.scalar_one_or_none()
        if wallet is None:
            # Create then re-select with lock to avoid a race between two
            # concurrent first-time wallet creations.
            wallet = Wallet(user_id=user_id, currency=currency_value)
            self.session.add(wallet)
            await self.session.flush()
            result = await self.session.execute(stmt)
            wallet = result.scalar_one()
        return wallet

    async def apply_ledger_entry(
        self,
        *,
        wallet: Wallet,
        entry_type: WalletEntryType,
        bucket: LedgerBalanceBucket,
        amount: int,
        idempotency_key: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
        note: str | None = None,
    ) -> LedgerEntry:
        """Apply a signed `amount` to the given bucket of `wallet`.

        Raises `app.services.money.InsufficientFundsError` if a debit
        (negative amount) would take the bucket below zero. The caller MUST
        have already locked `wallet` via `lock_wallet` in the current
        transaction to make this safe under concurrency.
        """
        from app.services.money import InsufficientFundsError  # local import: avoid cycle

        existing = await self.get_ledger_entry_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        current = self._bucket_value(wallet, bucket)
        new_value = current + amount
        if new_value < 0:
            raise InsufficientFundsError(
                available=current, requested=-amount, currency=wallet.currency
            )

        self._set_bucket_value(wallet, bucket, new_value)
        wallet.version += 1

        entry = LedgerEntry(
            created_at=dt.datetime.now(dt.UTC),
            wallet_id=wallet.id,
            user_id=wallet.user_id,
            currency=wallet.currency,
            entry_type=entry_type.value if isinstance(entry_type, WalletEntryType) else entry_type,
            bucket=bucket.value if isinstance(bucket, LedgerBalanceBucket) else bucket,
            amount=amount,
            balance_after=new_value,
            idempotency_key=idempotency_key,
            reference_type=reference_type,
            reference_id=reference_id,
            note=note,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_ledger_entry_by_idempotency_key(self, key: str) -> LedgerEntry | None:
        result = await self.session.execute(
            select(LedgerEntry).where(LedgerEntry.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def list_ledger_for_user(
        self, user_id: int, currency: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[LedgerEntry]:
        stmt = select(LedgerEntry).where(LedgerEntry.user_id == user_id)
        if currency:
            stmt = stmt.where(LedgerEntry.currency == currency)
        stmt = stmt.order_by(LedgerEntry.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_wallets_for_user(self, user_id: int) -> list[Wallet]:
        result = await self.session.execute(select(Wallet).where(Wallet.user_id == user_id))
        return list(result.scalars().all())

    @staticmethod
    def _bucket_value(wallet: Wallet, bucket: LedgerBalanceBucket | str) -> int:
        bucket_value = bucket.value if isinstance(bucket, LedgerBalanceBucket) else bucket
        return {
            "available": wallet.available_amount,
            "reserved": wallet.reserved_amount,
            "pending": wallet.pending_amount,
        }[bucket_value]

    @staticmethod
    def _set_bucket_value(wallet: Wallet, bucket: LedgerBalanceBucket | str, value: int) -> None:
        bucket_value = bucket.value if isinstance(bucket, LedgerBalanceBucket) else bucket
        if bucket_value == "available":
            wallet.available_amount = value
        elif bucket_value == "reserved":
            wallet.reserved_amount = value
        elif bucket_value == "pending":
            wallet.pending_amount = value
        else:
            raise ValueError(f"Unknown bucket {bucket_value!r}")
