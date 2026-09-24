"""Admin Dashboard: total/active/premium users, movies, views, orders,
successful payments, revenue by currency, pending reviews, recent errors.

All figures come straight from `StatisticsService.dashboard_summary`
(app/services/statistics_service.py), which is itself already covered by
service-layer tests -- this handler is purely presentational.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.statistics_service import StatisticsService

router = Router(name="admin_dashboard")


@router.callback_query(F.data == "adm:dash")
async def handle_admin_dashboard(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    stats = await StatisticsService(uow).dashboard_summary()

    revenue_lines = "\n".join(
        t(user.language, "admin_dashboard_revenue_line", currency=currency, amount=amount)
        for currency, amount in stats["revenue_by_currency"].items()
    ) or t(user.language, "admin_dashboard_no_errors")

    recent_errors = "\n".join(stats["recent_errors"]) or t(
        user.language, "admin_dashboard_no_errors"
    )

    text = (
        t(user.language, "admin_dashboard_title")
        + "\n\n"
        + t(
            user.language,
            "admin_dashboard_stats",
            total_users=stats["total_users"],
            active_users=stats["active_users"],
            premium_users=stats["premium_users"],
            movies_count=stats["movies_count"],
            views_count=stats["views_count"],
            orders_count=stats["total_orders"],
            paid_orders_count=stats["paid_orders"],
            revenue_lines=revenue_lines,
            pending_reviews=stats["pending_reviews"],
            recent_errors=recent_errors,
        )
    )

    await callback.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[admin_back_row(user.language)])
    )
    await callback.answer()
