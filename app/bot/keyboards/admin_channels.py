"""Keyboards for the admin Mandatory Channels section. Callback namespace: `ah:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row
from app.db.models.catalog import MandatoryChannel
from app.i18n import t


def admin_channels_menu_keyboard(
    channels: list[MandatoryChannel], language: str
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_channel_add_button"), callback_data="ah:add"
            )
        ],
    ]
    for c in channels:
        status = "✅" if c.is_active else "⛔"
        rows.append(
            [InlineKeyboardButton(text=f"{status} {c.title}", callback_data=f"ah:view:{c.id}")]
        )
    rows.append(admin_back_row(language, "adm:root"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_channel_detail_keyboard(channel: MandatoryChannel, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_channel_verify_button"),
                    callback_data=f"ah:verify:{channel.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_channel_toggle_button"),
                    callback_data=f"ah:toggle:{channel.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_channel_remove_button"),
                    callback_data=f"ah:remove:{channel.id}",
                )
            ],
            admin_back_row(language, "adm:chans"),
        ]
    )


def admin_channel_remove_confirm_keyboard(channel_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_confirm_button"),
                    callback_data=f"ah:remove_confirm:{channel_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_cancel_button"), callback_data=f"ah:view:{channel_id}"
                )
            ],
        ]
    )
