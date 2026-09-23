"""Global, admin-editable runtime settings.

A single-row-per-key table backing `app.services.settings_service`. Using a
key/value table (instead of hard-coded config) lets admins change global
policy (e.g. "does referral commission apply to renewals?", "global blogger
acquisition reward rate per 1000 joins", "allow promo stacking?") from the
admin panel without a deploy, while every historical order/reward still
reads its OWN frozen snapshot (see order.py / reward_accrual.py) so past
transactions are never retroactively altered.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Setting(IdMixin, TimestampMixin, Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


# Well-known setting keys (documented here so handlers/services/admin panel
# never hard-code raw strings in more than one place).
class SettingKey:
    REFERRAL_COMMISSION_ON_RENEWALS = "referral_commission_on_renewals"  # "true" | "false"
    BLOGGER_ACQUISITION_REWARD_PER_1000 = (
        "blogger_acquisition_reward_per_1000"  # integer minor units, global default
    )
    BLOGGER_ACQUISITION_REWARD_CURRENCY = "blogger_acquisition_reward_currency"  # e.g. "UZS"
    PROMO_STACKING_ALLOWED = "promo_stacking_allowed"  # "true" | "false"
    QUALIFIED_JOIN_MIN_ACCOUNT_AGE_HOURS = "qualified_join_min_account_age_hours"
