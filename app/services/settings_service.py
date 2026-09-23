"""Reads/writes admin-editable global settings (see app.db.models.settings)."""

from __future__ import annotations

from app.db.models.settings import SettingKey
from app.db.uow import UnitOfWork


class SettingsService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def referral_commission_on_renewals(self) -> bool:
        return await self.uow.settings.get_bool(
            SettingKey.REFERRAL_COMMISSION_ON_RENEWALS, default=False
        )

    async def set_referral_commission_on_renewals(self, enabled: bool) -> None:
        await self.uow.settings.set(
            SettingKey.REFERRAL_COMMISSION_ON_RENEWALS, "true" if enabled else "false"
        )

    async def global_blogger_reward_per_1000(self) -> tuple[int, str]:
        rate = await self.uow.settings.get_int(
            SettingKey.BLOGGER_ACQUISITION_REWARD_PER_1000, default=0
        )
        currency = (
            await self.uow.settings.get(SettingKey.BLOGGER_ACQUISITION_REWARD_CURRENCY) or "UZS"
        )
        return rate, currency

    async def set_global_blogger_reward_per_1000(self, rate: int, currency: str) -> None:
        await self.uow.settings.set(SettingKey.BLOGGER_ACQUISITION_REWARD_PER_1000, str(rate))
        await self.uow.settings.set(SettingKey.BLOGGER_ACQUISITION_REWARD_CURRENCY, currency)

    async def promo_stacking_allowed(self) -> bool:
        return await self.uow.settings.get_bool(SettingKey.PROMO_STACKING_ALLOWED, default=False)

    async def set_promo_stacking_allowed(self, enabled: bool) -> None:
        await self.uow.settings.set(
            SettingKey.PROMO_STACKING_ALLOWED, "true" if enabled else "false"
        )

    async def qualified_join_min_account_age_hours(self) -> int:
        return await self.uow.settings.get_int(
            SettingKey.QUALIFIED_JOIN_MIN_ACCOUNT_AGE_HOURS, default=0
        )
