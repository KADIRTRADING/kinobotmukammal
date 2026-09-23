"""Referral attribution.

A `Referral` row is created exactly once per referred user, the moment
their very first `/start` is attributed to a referrer. This is the anchor
that referral-commission and blogger-acquisition-reward accrual (see
`reward_accrual.py`) both hang off of. Uniqueness on `referred_user_id`
guarantees a user can only ever be attributed to a single referrer
(spec section 5: "one referrer only").
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class Referral(IdMixin, TimestampMixin, Base):
    __tablename__ = "referrals"

    referred_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    referrer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    attributed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Fraud / qualification bookkeeping -----------------------------------------------
    is_self_referral: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    suspicious_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    is_qualified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="True once this join passed anti-fraud qualification checks and is eligible for a "
        "blogger acquisition reward. Standard referral commission does NOT require qualification "
        "-- it only requires a verified purchase -- but blogger per-join rewards do.",
    )
    qualified_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disqualified_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)

    referrer_was_blogger_at_join: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    referred_user: Mapped[User] = relationship(
        "User", foreign_keys=[referred_user_id], back_populates="referral_as_referred"
    )
    referrer_user: Mapped[User] = relationship("User", foreign_keys=[referrer_user_id])
