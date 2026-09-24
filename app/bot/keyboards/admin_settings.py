"""Keyboards for the admin Settings & Audit section. Callback namespace: `as:`/`aa:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row
from app.i18n import t


def admin_settings_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_settings_toggle_renewals_button"),
                    callback_data="as:toggle_renewals",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_settings_toggle_stacking_button"),
                    callback_data="as:toggle_stacking",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_reward_rate_button"), callback_data="ab:rate"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_audit_button"), callback_data="adm:audit"
                )
            ],
            admin_back_row(language, "adm:root"),
        ]
    )


def admin_audit_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[admin_back_row(language, "adm:root")])
