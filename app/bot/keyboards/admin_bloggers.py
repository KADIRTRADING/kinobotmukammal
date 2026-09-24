"""Keyboards for the admin Bloggers/Referrals section. Callback namespace: `ab:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row, admin_pagination_row
from app.db.models.blogger import BloggerApplication, BloggerProfile
from app.i18n import t


def admin_bloggers_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_bloggers_pending_button"), callback_data="ab:pending:0"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_bloggers_active_button"), callback_data="ab:active:0"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_bloggers_suspicious_button"),
                callback_data="ab:suspicious:0",
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_reward_rate_button"), callback_data="ab:rate"
            )
        ],
        admin_back_row(language, "adm:root"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_blogger_pending_list_keyboard(
    apps: list[BloggerApplication], language: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"#{a.id}", callback_data=f"ab:view:{a.id}")] for a in apps]
    nav = admin_pagination_row(language, prefix="ab:pending:", page=page, total_pages=total_pages)
    if nav:
        rows.append(nav)
    rows.append(admin_back_row(language, "adm:bloggers"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_blogger_application_keyboard(application_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_blogger_approve_button"),
                    callback_data=f"ab:approve:{application_id}",
                ),
                InlineKeyboardButton(
                    text=t(language, "admin_blogger_reject_button"),
                    callback_data=f"ab:reject:{application_id}",
                ),
            ],
            admin_back_row(language, "adm:bloggers"),
        ]
    )


def admin_blogger_active_list_keyboard(
    profiles: list[BloggerProfile], language: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"user #{p.user_id}", callback_data=f"ab:activeview:{p.user_id}"
            )
        ]
        for p in profiles
    ]
    nav = admin_pagination_row(language, prefix="ab:active:", page=page, total_pages=total_pages)
    if nav:
        rows.append(nav)
    rows.append(admin_back_row(language, "adm:bloggers"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_blogger_profile_keyboard(profile: BloggerProfile, language: str) -> InlineKeyboardMarkup:
    action = (
        [
            InlineKeyboardButton(
                text=t(language, "admin_blogger_reactivate_button"),
                callback_data=f"ab:reactivate:{profile.user_id}",
            )
        ]
        if profile.status == "suspended"
        else [
            InlineKeyboardButton(
                text=t(language, "admin_blogger_suspend_button"),
                callback_data=f"ab:suspend:{profile.user_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=[action, admin_back_row(language, "adm:bloggers")])
