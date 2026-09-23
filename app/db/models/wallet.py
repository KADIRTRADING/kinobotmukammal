"""Wallet balances and the immutable ledger.

Design:
  - `Wallet` is a per-(user, currency) row holding three integer minor-unit
    counters: available, reserved, pending. It is a materialized *cache* of
    the ledger, updated only inside the same DB transaction as the ledger
    insert that justifies the change (see app.services.wallet_service).
  - `LedgerEntry` rows are NEVER updated or deleted after insert. Every
    balance mutation -- referral commission, gift, promo reservation, promo
    consumption, refund reversal, admin adjustment -- is represented as one
    or more ledger rows. Summing ledger rows for a wallet always reproduces
    the cached balances; this invariant is asserted in tests and by the
    reconciliation worker.
  - A CHECK constraint prevents `available_amount` (and reserved) from ever
    going negative at the database level, as a last line of defense beyond
    the application-level locking in the wallet service.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import Currency, LedgerBalanceBucket, WalletEntryType

if TYPE_CHECKING:
    from app.db.models.user import User


class Wallet(IdMixin, TimestampMixin, Base):
    __tablename__ = "wallets"
    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_wallets_user_currency"),
        CheckConstraint("available_amount >= 0", name="available_non_negative"),
        CheckConstraint("reserved_amount >= 0", name="reserved_non_negative"),
        CheckConstraint("pending_amount >= 0", name="pending_non_negative"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)

    available_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    reserved_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    pending_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    # Optimistic-lock version, incremented on every mutation, in addition to
    # SELECT ... FOR UPDATE row locking used by the wallet service.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship("User", back_populates="wallets")

    @property
    def total_amount(self) -> int:
        return self.available_amount + self.reserved_amount + self.pending_amount


class LedgerEntry(IdMixin, Base):
    """Append-only. `idempotency_key` gives external callers (webhooks) a
    safe way to guarantee "at most once" application even under retries."""

    __tablename__ = "ledger_entries"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_ledger_entries_idempotency_key"),
    )

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    wallet_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)

    entry_type: Mapped[WalletEntryType] = mapped_column(String(48), nullable=False)
    bucket: Mapped[LedgerBalanceBucket] = mapped_column(String(16), nullable=False)

    # Signed delta applied to the named bucket. Positive = credit, negative = debit.
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)

    balance_after: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="Snapshot of that bucket's balance immediately after this entry.",
    )

    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)

    reference_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True, doc="e.g. 'order', 'promo_code', 'gift', 'referral_commission'."
    )
    reference_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
