"""Keyboards for the admin Support section. Callback namespace: `asu:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row, admin_pagination_row
from app.db.models.support import SupportTicket
from app.i18n import t


def admin_support_list_keyboard(
    tickets: list[SupportTicket], language: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"#{tk.id} {tk.subject or ''}"[:40], callback_data=f"asu:view:{tk.id}"
            )
        ]
        for tk in tickets
    ]
    nav = admin_pagination_row(language, prefix="asu:list:", page=page, total_pages=total_pages)
    if nav:
        rows.append(nav)
    rows.append(admin_back_row(language, "adm:root"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_support_ticket_keyboard(ticket_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_support_reply_button"),
                    callback_data=f"asu:reply:{ticket_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_support_close_button"),
                    callback_data=f"asu:close:{ticket_id}",
                )
            ],
            admin_back_row(language, "adm:support"),
        ]
    )
