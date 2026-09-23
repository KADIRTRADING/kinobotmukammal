"""Premium subscription plans.

Every commercial parameter (price, referral %, blogger %, acquisition
reward toggle, discount cap) is configured *per plan* so that, e.g., a
1-week plan and a 1-month plan can carry entirely different commission
economics as required by spec section 3. Nothing here is ever hard-coded
at the handler/service level — all math reads from these columns (or from
an immutable snapshot copied out of them at purchase time, see
`app/db/models/order.py`).
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import Currency


class PremiumPlan(IdMixin, TimestampMixin, Base):
    __tablename__ = "premium_plans"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title_uz: Mapped[str] = mapped_column(String(128), nullable=False)
    title_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    title_en: Mapped[str] = mapped_column(String(128), nullable=False)

    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)

    price_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Integer minor units (e.g. UZS has no minor unit, so this is whole UZS).",
    )
    currency: Mapped[Currency] = mapped_column(
        String(8), nullable=False, default=Currency.UZS.value
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # --- Per-plan referral economics (spec section 3) ------------------------------
    standard_referral_percent: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Basis: percent*100, e.g. 1000 = 10.00%."
    )
    blogger_referral_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Percent*100. Bloggers may get a different (usually higher) rate.",
    )
    blogger_acquisition_reward_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether bloggers additionally earn per-qualified-join rewards for this plan's purchasers.",
    )
    referral_applies_to_renewals: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="If False, commission is only ever paid on a referred user's FIRST premium purchase across all plans. "
        "If True, every renewal/purchase also pays commission. This is a global-behavior flag intentionally "
        "duplicated per-plan so admins can special-case a plan later; the effective policy used at purchase time "
        "is read from app.config.settings.REFERRAL_COMMISSION_ON_RENEWALS unless overridden here (see referral service).",
    )

    # --- Promo eligibility caps ------------------------------------------------------
    max_discount_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        doc="Upper bound (0-100) a percent-discount promo may apply to this plan.",
    )
    promo_eligible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    description_uz: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description_ru: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description_en: Mapped[str | None] = mapped_column(String(512), nullable=True)

    def title(self, language: str) -> str:
        return {"uz": self.title_uz, "ru": self.title_ru, "en": self.title_en}.get(
            language, self.title_uz
        )

    @property
    def standard_referral_rate(self) -> float:
        return self.standard_referral_percent / 10_000

    @property
    def blogger_referral_rate(self) -> float:
        return self.blogger_referral_percent / 10_000
