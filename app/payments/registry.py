"""Central place that exposes only providers which are actually usable.

`app.admin` (provider status screen) and `app.bot.handlers.premium` both
call `PaymentRegistry.status_report()` / `get_enabled(code)` rather than
importing individual adapters, so there is exactly one source of truth for
"is this provider live, sandbox, or disabled".
"""

from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot

from app.config import Settings
from app.payments.base import PaymentProvider, ProviderDisabledError
from app.payments.click_provider import ClickProvider
from app.payments.stars import StarsProvider
from app.payments.stripe_provider import StripeProvider


@dataclass(frozen=True)
class ProviderStatus:
    code: str
    enabled: bool
    live: bool
    label: str


class PaymentRegistry:
    def __init__(self, settings: Settings, bot: Bot | None = None) -> None:
        self._settings = settings
        self._providers: dict[str, PaymentProvider] = {}
        if bot is not None:
            self._providers["telegram_stars"] = StarsProvider(settings, bot)
        self._providers["stripe"] = StripeProvider(settings)
        self._providers["click"] = ClickProvider(settings)

    def get(self, code: str) -> PaymentProvider:
        provider = self._providers.get(code)
        if provider is None:
            raise ProviderDisabledError(code)
        return provider

    def get_enabled(self, code: str) -> PaymentProvider:
        provider = self.get(code)
        if not provider.is_enabled():
            raise ProviderDisabledError(code)
        return provider

    def is_registered(self, code: str) -> bool:
        return code in self._providers

    def is_provider_enabled(self, code: str) -> bool:
        return self.is_registered(code) and self._providers[code].is_enabled()

    def status_report(self) -> list[ProviderStatus]:
        labels = {
            "telegram_stars": "Telegram Stars (in-app digital goods)",
            "stripe": "Stripe (independent web storefront)",
            "click": "Click (independent web storefront, Uzbekistan)",
        }
        report = []
        for code, provider in self._providers.items():
            report.append(
                ProviderStatus(
                    code=code,
                    enabled=provider.is_enabled(),
                    live=provider.is_live(),
                    label=labels.get(code, code),
                )
            )
        return report
