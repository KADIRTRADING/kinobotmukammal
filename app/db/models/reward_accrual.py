"""Reward accrual ledger anchors: referral commissions and blogger
acquisition rewards, each with an immutable policy snapshot and a status
that supports reversal on refund.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import Currency, RewardStatus


class ReferralCommission(IdMixin, TimestampMixin, Base):
    """Commission credited to a referrer (standard or blogger) after an
    eligible, verified premium purchase by their referred user.

    `order_id` + `commission_kind='purchase'` is unique so a single order
    can never generate the same commission twice, satisfying idempotent
    webhook processing even under retried/duplicate payment callbacks.
    """

    __tablename__ = "referral_commissions"
    __table_args__ = (UniqueConstraint("order_id", name="uq_referral_commissions_order_id"),)

    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    referral_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False
    )
    referrer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("premium_plans.id"), nullable=False)

    # --- Immutable snapshot of the policy applied at the time of this purchase ---
    commission_percent_snapshot: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="percent*100"
    )
    eligible_net_amount_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    was_blogger_rate_snapshot: Mapped[bool] = mapped_column(Integer, nullable=False, default=False)

    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)

    status: Mapped[RewardStatus] = mapped_column(
        String(16), nullable=False, default=RewardStatus.ACCRUED.value
    )
    reversed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_first_purchase_of_referred_user: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=True
    )


class BloggerAcquisitionReward(IdMixin, TimestampMixin, Base):
    """One row per QUALIFIED join, credited starting with the very first
    qualified user (never batched to wait for 1000). `referral_id` is
    unique so a join can never be rewarded twice.
    """

    __tablename__ = "blogger_acquisition_rewards"
    __table_args__ = (
        UniqueConstraint("referral_id", name="uq_blogger_acquisition_rewards_referral_id"),
    )

    referral_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("referrals.id", ondelete="CASCADE"), nullable=False
    )
    blogger_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )

    rate_per_1000_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Whole minor units credited for this single qualified join (post remainder-carry).",
    )
    remainder_micros_before: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remainder_micros_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="This blogger's Nth qualified join (1-indexed) at accrual time.",
    )

    status: Mapped[RewardStatus] = mapped_column(
        String(16), nullable=False, default=RewardStatus.ACCRUED.value
    )
    reversed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversal_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
