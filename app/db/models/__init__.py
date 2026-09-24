"""Import every model module so `Base.metadata` is fully populated for
Alembic autogenerate and for `Base.metadata.create_all()` in tests.
"""

from app.db.base import Base  # noqa: F401
from app.db.models.admin import Admin, AuditLog  # noqa: F401
from app.db.models.admin_grant import AdminGrant  # noqa: F401
from app.db.models.blogger import BloggerApplication, BloggerProfile  # noqa: F401
from app.db.models.broadcast import Broadcast, BroadcastRecipient  # noqa: F401
from app.db.models.catalog import Category, MandatoryChannel, Movie  # noqa: F401
from app.db.models.gift import Gift  # noqa: F401
from app.db.models.order import Entitlement, Order, ProviderEvent  # noqa: F401
from app.db.models.plan import PremiumPlan  # noqa: F401
from app.db.models.promo import PromoCode, PromoRedemption  # noqa: F401
from app.db.models.referral import Referral  # noqa: F401
from app.db.models.reward_accrual import BloggerAcquisitionReward, ReferralCommission  # noqa: F401
from app.db.models.settings import Setting, SettingKey  # noqa: F401
from app.db.models.support import SupportMessage, SupportTicket  # noqa: F401
from app.db.models.user import User  # noqa: F401
from app.db.models.wallet import LedgerEntry, Wallet  # noqa: F401

__all__ = [
    "Base",
    "Admin",
    "AuditLog",
    "AdminGrant",
    "BloggerApplication",
    "BloggerProfile",
    "Broadcast",
    "BroadcastRecipient",
    "Category",
    "MandatoryChannel",
    "Movie",
    "Gift",
    "Entitlement",
    "Order",
    "ProviderEvent",
    "PremiumPlan",
    "PromoCode",
    "PromoRedemption",
    "Referral",
    "BloggerAcquisitionReward",
    "ReferralCommission",
    "Setting",
    "SettingKey",
    "SupportMessage",
    "SupportTicket",
    "User",
    "LedgerEntry",
    "Wallet",
]
