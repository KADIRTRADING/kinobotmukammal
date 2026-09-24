"""Unit-of-work: bundles every repository behind a single object bound to
one AsyncSession/transaction, so services don't have to construct each
repository by hand.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.admin_grant_repo import AdminGrantRepository
from app.db.repositories.admin_repo import AdminRepository, AuditLogRepository
from app.db.repositories.blogger_repo import BloggerRepository
from app.db.repositories.broadcast_repo import BroadcastRepository
from app.db.repositories.catalog_repo import CatalogRepository
from app.db.repositories.gift_repo import GiftRepository
from app.db.repositories.order_repo import OrderRepository
from app.db.repositories.plan_repo import PlanRepository
from app.db.repositories.promo_repo import PromoRepository
from app.db.repositories.referral_repo import ReferralRepository
from app.db.repositories.reward_repo import RewardRepository
from app.db.repositories.settings_repo import SettingsRepository
from app.db.repositories.support_repo import SupportRepository
from app.db.repositories.user_repo import UserRepository
from app.db.repositories.wallet_repo import WalletRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.catalog = CatalogRepository(session)
        self.plans = PlanRepository(session)
        self.wallets = WalletRepository(session)
        self.referrals = ReferralRepository(session)
        self.bloggers = BloggerRepository(session)
        self.rewards = RewardRepository(session)
        self.orders = OrderRepository(session)
        self.promos = PromoRepository(session)
        self.gifts = GiftRepository(session)
        self.broadcasts = BroadcastRepository(session)
        self.support = SupportRepository(session)
        self.admins = AdminRepository(session)
        self.admin_grants = AdminGrantRepository(session)
        self.audit = AuditLogRepository(session)
        self.settings = SettingsRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()
