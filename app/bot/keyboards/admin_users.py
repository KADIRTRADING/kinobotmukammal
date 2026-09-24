"""Keyboards for the admin Users section. Callback namespace: `au:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row, admin_pagination_row
from app.db.models.plan import PremiumPlan
from app.db.models.user import User
from app.i18n import t


def admin_users_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[admin_back_row(language, "adm:root")])


def admin_user_search_results_keyboard(
    users: list[User], language: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{u.username or u.telegram_id}", callback_data=f"au:view:{u.id}"
            )
        ]
        for u in users
    ]
    nav = admin_pagination_row(language, prefix="au:results:", page=page, total_pages=total_pages)
    if nav:
        rows.append(nav)
    rows.append(admin_back_row(language, "adm:users"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_user_detail_keyboard(user: User, language: str) -> InlineKeyboardMarkup:
    block_row = (
        [
            InlineKeyboardButton(
                text=t(language, "admin_user_unblock_button"), callback_data=f"au:unblock:{user.id}"
            )
        ]
        if user.is_blocked
        else [
            InlineKeyboardButton(
                text=t(language, "admin_user_block_button"), callback_data=f"au:block:{user.id}"
            )
        ]
    )
    rows = [
        block_row,
        [
            InlineKeyboardButton(
                text=t(language, "admin_user_grant_premium_button"),
                callback_data=f"au:grant:{user.id}",
            )
        ],
    ]
    if user.is_premium_active:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "admin_user_revoke_premium_button"),
                    callback_data=f"au:revoke:{user.id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(language, "admin_user_gift_balance_button"),
                callback_data=f"au:gift:{user.id}",
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(language, "admin_user_orders_button"), callback_data=f"au:orders:{user.id}:0"
            )
        ]
    )
    rows.append(admin_back_row(language, "adm:users"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_user_plan_pick_keyboard(
    plans: list[PremiumPlan], user_id: int, language: str
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{p.code} — {p.price_amount} {p.currency}",
                callback_data=f"au:grantplan:{user_id}:{p.id}",
            )
        ]
        for p in plans
    ]
    rows.append(admin_back_row(language, f"au:view:{user_id}"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_user_orders_keyboard(
    user_id: int, language: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    nav = admin_pagination_row(
        language, prefix=f"au:orders:{user_id}:", page=page, total_pages=total_pages
    )
    rows = [nav] if nav else []
    rows.append(admin_back_row(language, f"au:view:{user_id}"))
    return InlineKeyboardMarkup(inline_keyboard=rows)
