"""Payment provider interface.

Every provider models a purchase as: create a server-priced charge/invoice
-> receive a provider callback/update -> verify authenticity -> return a
normalized `PaymentEvent` for `PurchaseService.confirm_payment`/
`refund_order` to act on. Providers NEVER accept a client-declared price;
`amount`/`currency` passed into `create_charge` always come from
`PurchaseService.create_order`'s server-side snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class PaymentEventType(str, Enum):
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_CANCELLED = "payment_cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ChargeHandle:
    """What a provider returns after creating a charge/invoice/session."""

    provider_reference: str
    checkout_payload: dict[str, Any]
    """Provider-specific data the bot/web layer needs to actually present
    the payment UI, e.g. a Telegram invoice payload, a Stripe Checkout
    Session URL, or a Click payment URL."""


@dataclass(frozen=True)
class PaymentEvent:
    provider_event_id: str
    event_type: PaymentEventType
    provider_reference: str | None
    order_uid: str | None
    raw_payload: dict[str, Any]
    verified: bool
    """True only if the event's authenticity was cryptographically/API
    verified (Telegram pre_checkout/successful_payment inherent trust,
    Stripe signature check, Click hash check). NEVER trust an event where
    verified is False."""


class PaymentProvider(Protocol):
    code: str

    def is_enabled(self) -> bool:
        """True only when the feature flag is on AND required credentials
        are present. A provider that returns False here must refuse to
        create charges."""
        ...

    def is_live(self) -> bool:
        """True only in a fully configured production/live credential
        mode. Sandboxes must return False so the UI/README can honestly
        label the provider "sandbox-only"."""
        ...

    async def create_charge(
        self,
        *,
        order_uid: str,
        amount: int,
        currency: str,
        description: str,
        buyer_telegram_id: int,
    ) -> ChargeHandle: ...

    async def parse_webhook(self, *, headers: dict[str, str], body: bytes) -> PaymentEvent:
        """Parse + verify an inbound webhook/update. Must NOT raise on a bad
        signature -- return `verified=False` so the caller can reject with a
        4xx and log, without leaking a stack trace to the caller."""
        ...

    async def refund(self, *, provider_reference: str, amount: int | None = None) -> bool:
        """Issue a refund via the provider's API. Returns True on success.
        Raises NotImplementedError if the provider has no refund API
        (e.g. Telegram Stars refunds are issued via a specific Bot API
        method that must be called with the ORIGINAL buyer's user id --
        see stars.py)."""
        ...


class ProviderDisabledError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(
            f"Payment provider '{code}' is disabled: missing feature flag or credentials. "
            "It will remain disabled until configured in .env and re-deployed."
        )
