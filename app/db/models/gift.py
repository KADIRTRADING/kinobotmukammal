"""Gifts: premium, balance, or promo codes given user-to-user or admin-to-user."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, UuidMixin
from app.db.models.enums import Currency, GiftKind


class Gift(IdMixin, UuidMixin, TimestampMixin, Base):
    __tablename__ = "gifts"

    kind: Mapped[GiftKind] = mapped_column(String(16), nullable=False)

    sender_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )
    sender_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    recipient_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )

    plan_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("premium_plans.id"), nullable=True
    )
    balance_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    balance_currency: Mapped[Currency | None] = mapped_column(String(8), nullable=True)
    promo_code_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("promo_codes.id"), nullable=True
    )

    cost_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_currency: Mapped[Currency | None] = mapped_column(String(8), nullable=True)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    entitlement_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("entitlements.id"), nullable=True
    )

    delivered_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
