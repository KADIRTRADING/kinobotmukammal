"""Shared building blocks for every admin-panel keyboard: pagination,
confirm/cancel rows, and the top-level admin menu.

Callback-data length: Telegram caps `callback_data` at 64 bytes. Every
callback prefix used across the admin panel is kept short (e.g. `adm:`,
`am:`, `ac:`, `ap:`) and numeric ids are passed as plain decimal integers,
which keeps every constructed string comfortably under the limit even for
64-bit ids. `paginate` centralizes page-index slicing so this constraint
only has to be respected in one place.
"""

from __future__ import annotations

from collections.abc import Sequence

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t

PAGE_SIZE = 8
"""Default number of list items per admin screen -- keeps messages short
and keyboards well within Telegram's inline-keyboard size limits."""


def admin_menu_root_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_dashboard_button"), callback_data="adm:dash"
            )
        ],
        [InlineKeyboardButton(text=t(language, "admin_movies_button"), callback_data="adm:movies")],
        [
            InlineKeyboardButton(
                text=t(language, "admin_categories_button"), callback_data="adm:cats"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_channels_button"), callback_data="adm:chans"
            )
        ],
        [InlineKeyboardButton(text=t(language, "admin_users_button"), callback_data="adm:users")],
        [InlineKeyboardButton(text=t(language, "admin_plans_button"), callback_data="adm:plans")],
        [InlineKeyboardButton(text=t(language, "admin_promos_button"), callback_data="adm:promos")],
        [
            InlineKeyboardButton(
                text=t(language, "admin_bloggers_button"), callback_data="adm:bloggers"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_support_button"), callback_data="adm:support"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_broadcasts_button"), callback_data="adm:bcast"
            )
        ],
        [InlineKeyboardButton(text=t(language, "admin_orders_button"), callback_data="adm:orders")],
        [
            InlineKeyboardButton(
                text=t(language, "admin_settings_button"), callback_data="adm:settings"
            )
        ],
        [InlineKeyboardButton(text=t(language, "admin_audit_button"), callback_data="adm:audit")],
        [InlineKeyboardButton(text=t(language, "admin_admins_button"), callback_data="adm:admins")],
        [
            InlineKeyboardButton(
                text=t(language, "admin_main_menu_button"), callback_data="adm:exit"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_back_row(language: str, back_callback: str = "adm:root") -> list[InlineKeyboardButton]:
    return [
        InlineKeyboardButton(
            text=t(language, "admin_back_to_panel_button"), callback_data=back_callback
        ),
        InlineKeyboardButton(text=t(language, "admin_main_menu_button"), callback_data="adm:exit"),
    ]


def admin_confirm_cancel_keyboard(
    language: str, confirm_cb: str, cancel_cb: str = "adm:cancel"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_confirm_button"), callback_data=confirm_cb
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_cancel_button"), callback_data=cancel_cb
                )
            ],
        ]
    )


def admin_pagination_row(
    language: str, *, prefix: str, page: int, total_pages: int
) -> list[InlineKeyboardButton]:
    """Builds a single Prev/Next row. `prefix` should already include a
    trailing separator, e.g. "am:list:" -> produces "am:list:<page>"."""
    buttons: list[InlineKeyboardButton] = []
    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                text=t(language, "admin_prev_page"), callback_data=f"{prefix}{page - 1}"
            )
        )
    if total_pages > 1:
        buttons.append(
            InlineKeyboardButton(
                text=t(language, "admin_page_nav", current=page + 1, total=total_pages),
                callback_data="adm:noop",
            )
        )
    if page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton(
                text=t(language, "admin_next_page"), callback_data=f"{prefix}{page + 1}"
            )
        )
    return buttons


def paginate(items: Sequence, page: int, page_size: int = PAGE_SIZE) -> tuple[list, int]:
    """Returns (items_on_this_page, total_pages). `page` is clamped into
    range so an out-of-range page (e.g. after items shrink) never raises."""
    total_pages = max(1, (len(items) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    start = page * page_size
    return list(items[start : start + page_size]), total_pages
