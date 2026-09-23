"""Telegram Stars payment adapter.

Telegram Stars ("XTR") is Telegram's own in-app currency for digital
goods, paid entirely inside the Telegram client via `sendInvoice` with
`currency="XTR"` and `provider_token=""` (Stars requires an empty provider
token per Bot API docs) followed by handling `pre_checkout_query` and
`successful_payment` updates. There is no external merchant account to
configure -- this is why `is_enabled()` only depends on the
`PAYMENTS_STARS_ENABLED` flag and a valid bot token, not on any additional
secret.

Refunds use `refundStarPayment(user_id, telegram_payment_charge_id)`, which
requires the ORIGINAL buyer's Telegram user id -- callers of `refund()`
here must pass that id, obtained from the original order.
"""

from __future__ import annotations

import hashlib
import json

from aiogram import Bot

from app.config import Settings
from app.payments.base import ChargeHandle, PaymentEvent, PaymentEventType


class StarsProvider:
    code = "telegram_stars"

    def __init__(self, settings: Settings, bot: Bot) -> None:
        self._settings = settings
        self._bot = bot

    def is_enabled(self) -> bool:
        return bool(self._settings.PAYMENTS_STARS_ENABLED and self._settings.BOT_TOKEN)

    def is_live(self) -> bool:
        # Telegram Stars has no separate "sandbox" mode distinct from the
        # bot token itself -- it is live the moment it's enabled with a
        # real bot token, matching Telegram's own documentation.
        return self.is_enabled()

    async def create_charge(
        self,
        *,
        order_uid: str,
        amount: int,
        currency: str,
        description: str,
        buyer_telegram_id: int,
    ) -> ChargeHandle:
        if not self.is_enabled():
            raise RuntimeError("Telegram Stars provider is disabled")
        if currency != "XTR":
            raise ValueError("Stars charges must be denominated in XTR")

        prices = [{"label": description[:32] or "Premium", "amount": amount}]
        payload = order_uid
        # The actual `sendInvoice` call is issued by the handler (it needs
        # the chat_id to send to); this adapter returns the structured
        # payload the handler should pass through, keeping aiogram Bot
        # calls that need a chat context out of the payments layer.
        return ChargeHandle(
            provider_reference=order_uid,
            checkout_payload={
                "title": description[:32] or "Premium subscription",
                "description": description[:255] or "Premium subscription",
                "payload": payload,
                "currency": "XTR",
                "prices": prices,
                "provider_token": "",
            },
        )

    async def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> PaymentEvent:
        """Stars payments don't arrive via a separate HTTP webhook -- they
        arrive as `successful_payment`/`pre_checkout_query` updates through
        the normal Telegram bot update stream (webhook or polling), already
        authenticated by Telegram's own delivery. This method exists to
        satisfy the common `PaymentProvider` interface for code that treats
        all providers uniformly (e.g. reconciliation); real-time handling is
        done directly in `app.bot.handlers.premium` via aiogram's
        `pre_checkout_query`/`successful_payment` handlers.
        """
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            return PaymentEvent(
                provider_event_id="invalid",
                event_type=PaymentEventType.UNKNOWN,
                provider_reference=None,
                order_uid=None,
                raw_payload={},
                verified=False,
            )
        sp = data.get("successful_payment") or {}
        charge_id = sp.get("telegram_payment_charge_id") or hashlib.sha256(body).hexdigest()
        return PaymentEvent(
            provider_event_id=charge_id,
            event_type=PaymentEventType.PAYMENT_SUCCEEDED if sp else PaymentEventType.UNKNOWN,
            provider_reference=charge_id,
            order_uid=sp.get("invoice_payload"),
            raw_payload=data,
            verified=bool(sp),
        )

    async def refund(
        self,
        *,
        provider_reference: str,
        amount: int | None = None,
        buyer_telegram_id: int | None = None,
    ) -> bool:
        if not self.is_enabled():
            raise RuntimeError("Telegram Stars provider is disabled")
        if buyer_telegram_id is None:
            raise ValueError("Stars refunds require the original buyer's telegram_id")
        # aiogram >=3.15 exposes Bot.refund_star_payment(user_id, telegram_payment_charge_id)
        await self._bot.refund_star_payment(
            user_id=buyer_telegram_id, telegram_payment_charge_id=provider_reference
        )
        return True
