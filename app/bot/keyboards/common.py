from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.i18n import t


def language_selection_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )


def main_menu_keyboard(language: str) -> ReplyKeyboardMarkup:
    rows = [
        [
            KeyboardButton(text=t(language, "menu_search_movie")),
            KeyboardButton(text=t(language, "menu_categories")),
        ],
        [
            KeyboardButton(text=t(language, "menu_premium")),
            KeyboardButton(text=t(language, "menu_balance")),
        ],
        [
            KeyboardButton(text=t(language, "menu_invite_friends")),
            KeyboardButton(text=t(language, "menu_my_promo_codes")),
        ],
        [
            KeyboardButton(text=t(language, "menu_gifts")),
            KeyboardButton(text=t(language, "menu_help")),
        ],
        [KeyboardButton(text=t(language, "menu_settings"))],
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def cancel_keyboard(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(language, "menu_cancel"))]], resize_keyboard=True
    )


def back_inline_button(language: str, callback_data: str = "nav:back") -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(language, "menu_back"), callback_data=callback_data)


def yes_no_keyboard(language: str, yes_cb: str, no_cb: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_attribution_yes"), callback_data=yes_cb
                ),
                InlineKeyboardButton(text=t(language, "promo_attribution_no"), callback_data=no_cb),
            ]
        ]
    )


def confirm_keyboard(
    language: str, confirm_cb: str, cancel_cb: str = "nav:cancel"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "premium_checkout_confirm"), callback_data=confirm_cb
                )
            ],
            [InlineKeyboardButton(text=t(language, "menu_cancel"), callback_data=cancel_cb)],
        ]
    )
