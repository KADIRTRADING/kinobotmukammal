from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def referral_menu_keyboard(language: str, *, show_blogger_cta: bool) -> InlineKeyboardMarkup:
    rows = []
    if show_blogger_cta:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "referral_become_blogger_button"),
                    callback_data="blogger:apply",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
