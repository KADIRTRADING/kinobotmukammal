"""Aggregate statistics for the admin dashboard and user-facing stat screens."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select

from app.db.models.catalog import Movie
from app.db.models.enums import OrderStatus
from app.db.models.order import Order, ProviderEvent
from app.db.models.user import User
from app.db.uow import UnitOfWork

ACTIVE_USER_WINDOW_DAYS = 7
RECENT_ERROR_WINDOW_HOURS = 24


class StatisticsService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def dashboard_summary(self) -> dict:
        """Everything the in-Telegram admin Dashboard screen needs, using
        ONLY data that genuinely exists in the schema -- there is no
        separate "system error log" table, so `recent_errors` is derived
        honestly from real failure signals already recorded: orders that
        failed and payment-provider events that raised a processing error,
        both within the last `RECENT_ERROR_WINDOW_HOURS` hours. Nothing
        here is invented or approximated with a placeholder.
        """
        session = self.uow.session
        now = dt.datetime.now(dt.UTC)
        active_since = now - dt.timedelta(days=ACTIVE_USER_WINDOW_DAYS)
        error_since = now - dt.timedelta(hours=RECENT_ERROR_WINDOW_HOURS)

        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        active_users = (
            await session.execute(
                select(func.count(User.id)).where(User.last_seen_at >= active_since)
            )
        ).scalar_one()
        premium_users = (
            await session.execute(
                select(func.count(User.id)).where(
                    User.premium_until.is_not(None), User.premium_until > now
                )
            )
        ).scalar_one()

        movies_count = (await session.execute(select(func.count(Movie.id)))).scalar_one()
        views_count = (
            await session.execute(select(func.coalesce(func.sum(Movie.view_count), 0)))
        ).scalar_one()

        total_orders = (await session.execute(select(func.count(Order.id)))).scalar_one()
        paid_orders = (
            await session.execute(
                select(func.count(Order.id)).where(Order.status == OrderStatus.PAID.value)
            )
        ).scalar_one()
        revenue_by_currency = (
            await session.execute(
                select(Order.currency, func.sum(Order.net_amount))
                .where(Order.status == OrderStatus.PAID.value)
                .group_by(Order.currency)
            )
        ).all()

        pending_reviews = await self._count_pending_reviews()
        recent_errors = await self._recent_error_summaries(error_since)

        return {
            "total_users": int(total_users),
            "active_users": int(active_users),
            "premium_users": int(premium_users),
            "movies_count": int(movies_count),
            "views_count": int(views_count),
            "total_orders": int(total_orders),
            "paid_orders": int(paid_orders),
            "revenue_by_currency": {row[0]: int(row[1] or 0) for row in revenue_by_currency},
            "pending_reviews": pending_reviews,
            "recent_errors": recent_errors,
        }

    async def _count_pending_reviews(self) -> int:
        """Sum of every admin review queue: suspicious referrals, pending
        promo attribution links, and pending blogger applications. Open
        support tickets are shown separately in the Support section, so
        they're intentionally excluded here to avoid double-counting a
        different kind of "pending" work."""
        suspicious = await self.uow.referrals.count_suspicious()
        pending_promos = await self.uow.promos.count_pending_moderation()
        pending_bloggers = await self.uow.bloggers.count_pending()
        return suspicious + pending_promos + pending_bloggers

    async def _recent_error_summaries(self, since: dt.datetime) -> list[str]:
        session = self.uow.session
        failed_orders = (
            await session.execute(
                select(func.count(Order.id)).where(
                    Order.status == OrderStatus.FAILED.value, Order.created_at >= since
                )
            )
        ).scalar_one()
        failed_events = (
            await session.execute(
                select(func.count(ProviderEvent.id)).where(
                    ProviderEvent.processing_error.is_not(None), ProviderEvent.received_at >= since
                )
            )
        ).scalar_one()

        summaries: list[str] = []
        if failed_orders:
            summaries.append(f"{int(failed_orders)} failed orders ({RECENT_ERROR_WINDOW_HOURS}h)")
        if failed_events:
            summaries.append(
                f"{int(failed_events)} provider event errors ({RECENT_ERROR_WINDOW_HOURS}h)"
            )
        return summaries

    async def referrer_stats(self, referrer_user_id: int) -> dict:
        from app.services.referral_service import ReferralService

        return await ReferralService(self.uow).stats_for_referrer(referrer_user_id)
