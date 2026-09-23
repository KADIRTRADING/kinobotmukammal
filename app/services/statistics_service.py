"""Aggregate statistics for the admin dashboard and user-facing stat screens."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select

from app.db.models.enums import OrderStatus
from app.db.models.order import Order
from app.db.models.user import User
from app.db.uow import UnitOfWork


class StatisticsService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def dashboard_summary(self) -> dict:
        session = self.uow.session
        total_users = (await session.execute(select(func.count(User.id)))).scalar_one()
        premium_users = (
            await session.execute(
                select(func.count(User.id)).where(
                    User.premium_until.is_not(None), User.premium_until > dt.datetime.now(dt.UTC)
                )
            )
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

        return {
            "total_users": int(total_users),
            "premium_users": int(premium_users),
            "total_orders": int(total_orders),
            "paid_orders": int(paid_orders),
            "revenue_by_currency": {row[0]: int(row[1] or 0) for row in revenue_by_currency},
        }

    async def referrer_stats(self, referrer_user_id: int) -> dict:
        from app.services.referral_service import ReferralService

        return await ReferralService(self.uow).stats_for_referrer(referrer_user_id)
