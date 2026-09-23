"""Shared enumerations used across persistent models.

Kept in one module so services, repositories, and Alembic migrations
reference the exact same string values (SQLAlchemy Enum columns are
persisted by *name*, not by Python identity).
"""

from __future__ import annotations

import enum


class Language(str, enum.Enum):
    UZ = "uz"
    RU = "ru"
    EN = "en"


class AdminRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"


class Currency(str, enum.Enum):
    """Supported settlement currencies. Balances are NEVER converted between
    these — a wallet holds one row per (user, currency)."""

    UZS = "UZS"
    USD = "USD"
    XTR = "XTR"  # Telegram Stars


class MovieAccessType(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"


class MoviePublicationState(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class OrderKind(str, enum.Enum):
    PREMIUM_PURCHASE = "premium_purchase"
    PREMIUM_GIFT = "premium_gift"
    PROMO_TOPUP_PURCHASE = "promo_topup_purchase"  # remainder payment on a discount promo


class PaymentProviderCode(str, enum.Enum):
    TELEGRAM_STARS = "telegram_stars"
    STRIPE = "stripe"
    CLICK = "click"
    WALLET = "wallet"  # internal ledger settlement, no external provider


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class EntitlementSource(str, enum.Enum):
    PURCHASE = "purchase"
    GIFT = "gift"
    PROMO = "promo"
    ADMIN_GRANT = "admin_grant"


class BloggerApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class BloggerProfileStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class RewardStatus(str, enum.Enum):
    ACCRUED = "accrued"
    REVERSED = "reversed"
    REJECTED = "rejected"


class WalletEntryType(str, enum.Enum):
    REFERRAL_COMMISSION = "referral_commission"
    BLOGGER_ACQUISITION_REWARD = "blogger_acquisition_reward"
    ADMIN_GIFT = "admin_gift"
    USER_GIFT_SENT = "user_gift_sent"
    USER_GIFT_RECEIVED = "user_gift_received"
    PROMO_CODE_FUNDING_RESERVE = "promo_code_funding_reserve"
    PROMO_CODE_FUNDING_RELEASE = "promo_code_funding_release"
    PROMO_CODE_FUNDING_CONSUME = "promo_code_funding_consume"
    WALLET_PREMIUM_PURCHASE = "wallet_premium_purchase"
    COMMISSION_REVERSAL = "commission_reversal"
    REWARD_REVERSAL = "reward_reversal"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class LedgerBalanceBucket(str, enum.Enum):
    """Which balance bucket a ledger entry affects."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    PENDING = "pending"


class PromoIssuerType(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    BLOGGER = "blogger"


class PromoKind(str, enum.Enum):
    FULL_PREMIUM = "full_premium"
    PERCENT_DISCOUNT = "percent_discount"


class PromoAttributionStatus(str, enum.Enum):
    NONE = "none"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class PromoModerationStatus(str, enum.Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class GiftKind(str, enum.Enum):
    PREMIUM = "premium"
    BALANCE = "balance"
    PROMO_CODE = "promo_code"


class BroadcastTarget(str, enum.Enum):
    ALL = "all"
    PREMIUM = "premium"
    FREE = "free"
    LANGUAGE = "language"
    CUSTOM_IDS = "custom_ids"


class BroadcastStatus(str, enum.Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BroadcastRecipientStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class SupportTicketStatus(str, enum.Enum):
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SupportSenderType(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class BloggerStatusCache(str, enum.Enum):
    NONE = "none"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
