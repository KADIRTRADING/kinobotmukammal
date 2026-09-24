"""Keyboards for the admin "👑 Admins" section. Callback namespace: `aa:`.

Every mutating callback here (`aa:grant_confirm:`, `aa:revoke:`,
`aa:revoke_confirm:`) is additionally re-checked against
`is_owner_admin` inside the handler body (see
`app.bot.handlers.admin.admins`) -- the keyboard only ever being SHOWN to
an owner is a UX nicety, never the security boundary, exactly like every
other admin-panel keyboard in this codebase.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row
from app.db.models.admin_grant import AdminGrant
from app.i18n import t


def admin_admins_menu_keyboard(language: str, *, is_owner: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_admins_list_button"), callback_data="aa:list"
            )
        ]
    ]
    if is_owner:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "admin_admins_add_button"), callback_data="aa:add"
                )
            ]
        )
    rows.append(admin_back_row(language, "adm:root"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_admins_list_keyboard(
    grants: list[AdminGrant], language: str, *, is_owner: bool
) -> InlineKeyboardMarkup:
    rows = []
    if is_owner:
        for g in grants:
            if not g.is_active:
                continue
            label = g.label or str(g.telegram_id)
            rows.append(
                [
                    InlineKeyboardButton(
                        text=t(language, "admin_admins_revoke_row", label=label),
                        callback_data=f"aa:revoke:{g.telegram_id}",
                    )
                ]
            )
    rows.append(admin_back_row(language, "adm:admins"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_admins_revoke_confirm_keyboard(telegram_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_confirm_button"),
                    callback_data=f"aa:revoke_confirm:{telegram_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_cancel_button"), callback_data="aa:list"
                )
            ],
        ]
    )


def admin_admins_grant_confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_confirm_button"), callback_data="aa:grant_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_cancel_button"), callback_data="adm:cancel"
                )
            ],
        ]
    )
