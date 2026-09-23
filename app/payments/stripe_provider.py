"""Stripe payment adapter — independent WEB storefront channel only.

IMPORTANT (compliance, spec section 4): this adapter must NEVER be used to
sell Telegram-bot digital goods to bot users as a way of routing around
Telegram's in-app digital-goods payment rules. It is wired ONLY into
`app.api.storefront`, a separate web checkout surface, and is gated by
`STOREFRONT_ENABLED` in addition to `PAYMENTS_STRIPE_ENABLED`. See
README.md "Payments and platform compliance" for the full policy.

`is_enabled()`/`is_live()` are strict: a missing API key or webhook secret
keeps the provider disabled even if the feature flag is on, so the app
never pretends Stripe is live with placeholder credentials.
"""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.payments.base import ChargeHandle, PaymentEvent, PaymentEventType


class StripeProvider:
    code = "stripe"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None
        if settings.PAYMENTS_STRIPE_ENABLED and settings.STRIPE_API_KEY:
            try:
                import stripe

                stripe.api_key = settings.STRIPE_API_KEY
                self._client = stripe
            except ImportError:
                self._client = None

    def is_enabled(self) -> bool:
        return bool(
            self._settings.PAYMENTS_STRIPE_ENABLED
            and self._settings.STOREFRONT_ENABLED
            and self._settings.STRIPE_API_KEY
            and self._settings.STRIPE_WEBHOOK_SECRET
            and self._client is not None
        )

    def is_live(self) -> bool:
        return self.is_enabled() and self._settings.STRIPE_MODE == "live"

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
            from app.payments.base import ProviderDisabledError

            raise ProviderDisabledError(self.code)

        session = self._client.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": description[:200]},
                        "unit_amount": amount,
                    },
                    "quantity": 1,
                }
            ],
            client_reference_id=order_uid,
            metadata={"order_uid": order_uid, "buyer_telegram_id": str(buyer_telegram_id)},
            success_url=f"{self._settings.PUBLIC_BASE_URL}/storefront/success?order={order_uid}",
            cancel_url=f"{self._settings.PUBLIC_BASE_URL}/storefront/cancel?order={order_uid}",
        )
        return ChargeHandle(
            provider_reference=session["id"],
            checkout_payload={"checkout_url": session["url"]},
        )

    async def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> PaymentEvent:
        if self._client is None:
            return PaymentEvent(
                provider_event_id="disabled",
                event_type=PaymentEventType.UNKNOWN,
                provider_reference=None,
                order_uid=None,
                raw_payload={},
                verified=False,
            )
        sig = headers.get("stripe-signature", "")
        try:
            event = self._client.Webhook.construct_event(
                body, sig, self._settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception:
            return PaymentEvent(
                provider_event_id="invalid_signature",
                event_type=PaymentEventType.UNKNOWN,
                provider_reference=None,
                order_uid=None,
                raw_payload={},
                verified=False,
            )

        obj = event["data"]["object"]
        order_uid = (obj.get("metadata") or {}).get("order_uid") or obj.get("client_reference_id")
        event_type_map = {
            "checkout.session.completed": PaymentEventType.PAYMENT_SUCCEEDED,
            "checkout.session.expired": PaymentEventType.PAYMENT_CANCELLED,
            "payment_intent.payment_failed": PaymentEventType.PAYMENT_FAILED,
            "charge.refunded": PaymentEventType.REFUNDED,
            "charge.dispute.created": PaymentEventType.DISPUTED,
        }
        return PaymentEvent(
            provider_event_id=event["id"],
            event_type=event_type_map.get(event["type"], PaymentEventType.UNKNOWN),
            provider_reference=obj.get("id"),
            order_uid=order_uid,
            raw_payload=event,
            verified=True,
        )

    async def refund(self, *, provider_reference: str, amount: int | None = None) -> bool:
        if not self.is_enabled():
            from app.payments.base import ProviderDisabledError

            raise ProviderDisabledError(self.code)
        kwargs: dict[str, Any] = {"payment_intent": provider_reference}
        if amount is not None:
            kwargs["amount"] = amount
        self._client.Refund.create(**kwargs)
        return True
