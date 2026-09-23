"""Click (click.uz) payment adapter — independent WEB storefront channel only.

Same compliance boundary as Stripe (see stripe_provider.py): Click is wired
only into the separate `app.api.storefront` web checkout, gated by both
`PAYMENTS_CLICK_ENABLED` and `STOREFRONT_ENABLED`, and is never used to
sell Telegram-bot digital goods.

Click's "Shop API" merchant webhook protocol (per Click's public merchant
integration documentation, e.g. https://docs.click.uz and the reference
implementations published at
https://github.com/click-llc/click-integration-php and
https://github.com/samarbadriddin0v/click-uz-integration-nodejs) sends two
sequential callbacks per transaction, `action=0` (Prepare) then `action=1`
(Complete), each carrying a `sign_string` that the merchant must recompute
and compare:

    sign_string = md5(
        click_trans_id + service_id + SECRET_KEY + merchant_trans_id +
        (merchant_prepare_id if action == Complete else "") +
        amount + action + sign_time
    )

A request whose recomputed signature doesn't match is rejected with
`error=-1` ("SIGN CHECK FAILED") and never touched further. This module
implements exactly that check; nothing here treats an unverified callback
as proof of payment (spec section 4: "Never trust ... a checkout success
URL as payment proof" — Click's redirect-back URL is informational only,
the merchant webhook is the sole source of truth here, consistent with
Click's own documented integration flow).
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.config import Settings
from app.payments.base import ChargeHandle, PaymentEvent, PaymentEventType


class ClickActionCode:
    PREPARE = 0
    COMPLETE = 1


class ClickErrorCode:
    SUCCESS = 0
    SIGN_CHECK_FAILED = -1
    TRANSACTION_NOT_FOUND = -6
    ALREADY_PAID = -4
    USER_NOT_FOUND = -5


class ClickProvider:
    code = "click"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def is_enabled(self) -> bool:
        s = self._settings
        return bool(
            s.PAYMENTS_CLICK_ENABLED
            and s.STOREFRONT_ENABLED
            and s.CLICK_MERCHANT_ID
            and s.CLICK_SERVICE_ID
            and s.CLICK_SECRET_KEY
        )

    def is_live(self) -> bool:
        return self.is_enabled() and self._settings.CLICK_MODE == "live"

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
        s = self._settings
        # Click's hosted checkout link format (my.click.uz/services/pay):
        checkout_url = (
            "https://my.click.uz/services/pay"
            f"?service_id={s.CLICK_SERVICE_ID}"
            f"&merchant_id={s.CLICK_MERCHANT_ID}"
            f"&amount={amount}"
            f"&transaction_param={order_uid}"
            f"&return_url={s.PUBLIC_BASE_URL}/storefront/success?order={order_uid}"
        )
        return ChargeHandle(
            provider_reference=order_uid, checkout_payload={"checkout_url": checkout_url}
        )

    def _expected_sign(
        self,
        *,
        click_trans_id: str,
        merchant_trans_id: str,
        amount: str,
        action: str,
        sign_time: str,
        merchant_prepare_id: str | None = None,
    ) -> str:
        s = self._settings
        parts = [click_trans_id, s.CLICK_SERVICE_ID, s.CLICK_SECRET_KEY, merchant_trans_id]
        if merchant_prepare_id is not None:
            parts.append(merchant_prepare_id)
        parts.extend([amount, action, sign_time])
        return hashlib.md5("".join(parts).encode("utf-8")).hexdigest()

    async def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> PaymentEvent:
        """Click posts `application/x-www-form-urlencoded` fields; the
        FastAPI route is responsible for handing us the parsed dict via
        `raw_payload` semantics -- here we accept an already-decoded form
        as JSON bytes for uniformity with the other adapters (the webhook
        route performs `dict(await request.form())` then `json.dumps(...)`
        before calling this, see app/api/webhooks/click.py)."""
        import json

        try:
            data: dict[str, Any] = json.loads(body.decode("utf-8"))
        except Exception:
            return PaymentEvent("invalid_body", PaymentEventType.UNKNOWN, None, None, {}, False)

        required = [
            "click_trans_id",
            "merchant_trans_id",
            "amount",
            "action",
            "sign_time",
            "sign_string",
        ]
        if not all(k in data for k in required):
            return PaymentEvent("missing_fields", PaymentEventType.UNKNOWN, None, None, data, False)

        expected = self._expected_sign(
            click_trans_id=str(data["click_trans_id"]),
            merchant_trans_id=str(data["merchant_trans_id"]),
            amount=str(data["amount"]),
            action=str(data["action"]),
            sign_time=str(data["sign_time"]),
            merchant_prepare_id=(
                str(data["merchant_prepare_id"]) if data.get("merchant_prepare_id") else None
            ),
        )
        verified = expected == str(data.get("sign_string", ""))

        action = str(data.get("action"))
        event_type = (
            PaymentEventType.PAYMENT_SUCCEEDED
            if action == str(ClickActionCode.COMPLETE)
            else PaymentEventType.UNKNOWN
        )
        if str(data.get("error", "0")) not in ("0",):
            event_type = PaymentEventType.PAYMENT_FAILED

        return PaymentEvent(
            provider_event_id=str(data.get("click_trans_id")),
            event_type=event_type,
            provider_reference=str(data.get("click_trans_id")),
            order_uid=str(data.get("merchant_trans_id")),
            raw_payload=data,
            verified=verified,
        )

    async def refund(self, *, provider_reference: str, amount: int | None = None) -> bool:
        # Click does not expose a self-service programmatic refund API for
        # Shop API merchants as of this writing; refunds are processed by
        # contacting Click merchant support. Documented here rather than
        # faked so admins know to use the manual process.
        raise NotImplementedError(
            "Click has no self-service refund API for Shop API merchants; "
            "process refunds via Click merchant support and record the outcome manually "
            "in the admin panel (Orders > mark refunded)."
        )
