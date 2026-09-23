"""Orders, provider events, and entitlements.

An `Order` snapshots everything needed to reproduce exactly what the buyer
was charged and what policy applied, so later admin changes to plan price
or commission rates never retroactively alter a completed purchase (spec
section 3). `ProviderEvent` records every inbound webhook/update for
idempotent processing and audit; `Entitlement` records the resulting
premium grant, tied 1:1 to the order/gift/promo that created it.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    BigInteger,
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
    EntitlementSource,
    OrderKind,
    OrderStatus,
    PaymentProviderCode,
)


class Order(IdMixin, UuidMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    buyer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    kind: Mapped[OrderKind] = mapped_column(String(32), nullable=False)

    plan_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("premium_plans.id"), nullable=True
    )

    # --- Immutable pricing snapshot, taken at order-creation time -------------------
    plan_price_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[Currency] = mapped_column(String(8), nullable=False)
    discount_percent_applied: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    promo_code_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("promo_codes.id"), nullable=True
    )
    gross_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="plan_price_snapshot before discount."
    )
    net_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, doc="Amount actually charged to the buyer."
    )

    standard_referral_percent_snapshot: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    blogger_referral_percent_snapshot: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    blogger_acquisition_reward_enabled_snapshot: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=True
    )

    provider_code: Mapped[PaymentProviderCode] = mapped_column(String(32), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        String(16), nullable=False, default=OrderStatus.PENDING.value
    )

    # Recipient differs from buyer for gifted premium.
    recipient_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=True
    )

    provider_reference: Mapped[str | None] = mapped_column(
        String(256), nullable=True, doc="Provider-side charge/session/invoice id, once known."
    )

    paid_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refunded_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    refund_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProviderEvent(IdMixin, Base):
    """Every inbound payment-provider webhook/update, kept verbatim (as JSON)
    for idempotent processing (`provider_code`+`provider_event_id` unique)
    and for dispute/audit investigation.
    """

    __tablename__ = "provider_events"
    __table_args__ = (
        UniqueConstraint(
            "provider_code", "provider_event_id", name="uq_provider_events_code_event_id"
        ),
    )

    received_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provider_code: Mapped[PaymentProviderCode] = mapped_column(String(32), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(256), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("orders.id"), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(Integer, nullable=False, default=False)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Entitlement(IdMixin, TimestampMixin, Base):
    """A single premium grant. `source_reference` links back to the order,
    gift, or promo redemption that created it. Activation happens exactly
    once per (source_type, source_reference) pair -- enforced by the unique
    constraint below plus a service-level advisory check.
    """

    __tablename__ = "entitlements"
    __table_args__ = (
        UniqueConstraint("source", "source_reference", name="uq_entitlements_source_reference"),
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("premium_plans.id"), nullable=False)

    source: Mapped[EntitlementSource] = mapped_column(String(16), nullable=False)
    source_reference: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Order uid, gift uid, or promo redemption uid that granted this entitlement.",
    )

    starts_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    granted_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
