"""Prepaid promo codes (full-premium and percent-discount) and redemptions.

Funding model (spec section 7):
  - A USER-created code reserves/debits the issuer's wallet balance
    atomically and in full at creation time for the maximum possible
    liability (activations * cost-per-activation). This liability lives in
    the issuer's `reserved` wallet bucket, NOT in a platform pool.
  - An ADMIN-created code is platform-funded and carries no wallet
    reservation; `issuer_type=ADMIN` and `issuer_user_id IS NULL`.
  - `remaining_uses` is decremented atomically (SELECT ... FOR UPDATE) on
    each redemption; a CHECK constraint additionally prevents it from ever
    going negative, which is what makes "two activations from one promo use"
    structurally impossible even under a race.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, UuidMixin
from app.db.models.enums import (
    Currency,
    PromoAttributionStatus,
    PromoIssuerType,
    PromoKind,
    PromoModerationStatus,
)


class PromoCode(IdMixin, UuidMixin, TimestampMixin, Base):
    __tablename__ = "promo_codes"
    __table_args__ = (
        CheckConstraint("remaining_uses >= 0", name="remaining_uses_non_negative"),
        CheckConstraint("max_uses > 0", name="max_uses_positive"),
    )

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)

    issuer_type: Mapped[PromoIssuerType] = mapped_column(String(16), nullable=False)
    issuer_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("premium_plans.id"), nullable=False)
    kind: Mapped[PromoKind] = mapped_column(String(24), nullable=False)
    discount_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="0 for FULL_PREMIUM (buyer pays nothing); 1-100 for PERCENT_DISCOUNT.",
    )

    max_uses: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_uses: Mapped[int] = mapped_column(Integer, nullable=False)

    # --- Funding bookkeeping (only meaningful when issuer_type != ADMIN) ------------
    funding_currency: Mapped[Currency | None] = mapped_column(String(8), nullable=True)
    cost_per_activation: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="What ONE redemption costs the issuer, in minor units.",
    )
    total_reserved_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_funds_released: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    expires_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    moderation_status: Mapped[PromoModerationStatus] = mapped_column(
        String(16), nullable=False, default=PromoModerationStatus.AUTO_APPROVED.value
    )
    moderation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Attribution link (spec section 7: "Add an attribution link?") --------------
    attribution_label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    attribution_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    attribution_telegram_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attribution_status: Mapped[PromoAttributionStatus] = mapped_column(
        String(16), nullable=False, default=PromoAttributionStatus.NONE.value
    )

    @property
    def is_redeemable(self) -> bool:
        if not self.is_active or self.remaining_uses <= 0:
            return False
        if self.moderation_status not in (
            PromoModerationStatus.AUTO_APPROVED,
            PromoModerationStatus.APPROVED,
        ):
            return False
        if self.expires_at and self.expires_at <= dt.datetime.now(dt.UTC):
            return False
        return True


class PromoRedemption(IdMixin, UuidMixin, TimestampMixin, Base):
    __tablename__ = "promo_redemptions"
    __table_args__ = (
        UniqueConstraint(
            "promo_code_id", "redeemer_user_id", name="uq_promo_redemptions_code_user"
        ),
    )

    promo_code_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False
    )
    redeemer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    order_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("orders.id"), nullable=True)

    discount_percent_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    issuer_cost_charged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    buyer_amount_paid: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
