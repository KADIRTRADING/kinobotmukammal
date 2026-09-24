"""Keyboards for the admin Categories section. Callback namespace: `ac:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row
from app.db.models.catalog import Category
from app.i18n import t


def admin_categories_menu_keyboard(
    categories: list[Category], language: str
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_category_add_button"), callback_data="ac:add"
            )
        ],
    ]
    for c in categories:
        status = "✅" if c.is_active else "⛔"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {c.title_uz} (#{c.sort_order})", callback_data=f"ac:view:{c.id}"
                )
            ]
        )
    rows.append(admin_back_row(language, "adm:root"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_category_detail_keyboard(category: Category, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_category_move_up_button"),
                    callback_data=f"ac:up:{category.id}",
                ),
                InlineKeyboardButton(
                    text=t(language, "admin_category_move_down_button"),
                    callback_data=f"ac:down:{category.id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_category_toggle_button"),
                    callback_data=f"ac:toggle:{category.id}",
                )
            ],
            admin_back_row(language, "adm:cats"),
        ]
    )
