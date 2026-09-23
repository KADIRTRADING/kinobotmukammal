from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


def gifts_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "gift_send_premium_button"), callback_data="gift:send_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "gift_send_balance_button"), callback_data="gift:send_balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "gift_received_list_button"), callback_data="gift:received"
                )
            ],
        ]
    )


def gift_confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "gift_confirm_button"), callback_data="gift_confirm:yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "menu_cancel"), callback_data="gift_confirm:no"
                )
            ],
        ]
    )
