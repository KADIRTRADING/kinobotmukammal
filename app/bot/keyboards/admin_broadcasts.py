"""Keyboards for the admin Broadcasts section. Callback namespace: `abc:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row
from app.db.models.broadcast import Broadcast
from app.i18n import t


def admin_broadcasts_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_broadcast_create_button"), callback_data="abc:create"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_broadcast_active_button"), callback_data="abc:active"
            )
        ],
        admin_back_row(language, "adm:root"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_broadcast_target_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_broadcast_target_all_button"),
                    callback_data="abc:target:all",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_broadcast_target_premium_button"),
                    callback_data="abc:target:premium",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_broadcast_target_free_button"),
                    callback_data="abc:target:free",
                )
            ],
        ]
    )


def admin_broadcast_confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_broadcast_confirm_send_button"),
                    callback_data="abc:send",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_cancel_button"), callback_data="abc:cancel_compose"
                )
            ],
        ]
    )


def admin_broadcast_active_list_keyboard(
    broadcasts: list[Broadcast], language: str
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=f"#{b.id} ({b.status})", callback_data=f"abc:view:{b.id}"),
            InlineKeyboardButton(
                text=t(language, "admin_broadcast_cancel_button"),
                callback_data=f"abc:cancelrun:{b.id}",
            ),
        ]
        for b in broadcasts
    ]
    rows.append(admin_back_row(language, "adm:bcast"))
    return InlineKeyboardMarkup(inline_keyboard=rows)
