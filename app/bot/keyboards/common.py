from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.config import get_settings
from app.core.admin_access import is_superadmin_id
from app.db.uow import UnitOfWork
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


def main_menu_keyboard(language: str, *, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """The normal user menu. `is_admin` adds an EXTRA "🛠 Admin panel" row
    for allowlisted Telegram IDs only -- callers must pass this based on
    `app.core.admin_access.is_superadmin_id(user.telegram_id, settings)`,
    never based on anything the user could influence. This flag only
    controls whether the button is *shown*; every admin action is still
    independently re-authorized server-side on every message/callback (see
    app.bot.filters.admin_filter.AdminAccessFilter) -- hiding this button
    from everyone else is a UX nicety, not the security boundary.
    """
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
    if is_admin:
        rows.append([KeyboardButton(text=t(language, "admin_menu_button"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


async def main_menu_keyboard_for_telegram_id(
    language: str, telegram_id: int | None, uow: UnitOfWork
) -> ReplyKeyboardMarkup:
    """Convenience wrapper used by every handler that renders the main
    menu: resolves `is_admin` from the live env allowlist AND the
    runtime-grantable `admin_grants` table, so callers never have to
    import `app.core.admin_access` (or query grants) themselves. This is
    the preferred entrypoint over calling `main_menu_keyboard` directly
    with a hand-computed `is_admin` value.

    Requires `uow` (every handler already has one injected by
    `DbSessionMiddleware`) because checking whether `telegram_id` is a
    runtime-granted admin means reading the `admin_grants` table -- unlike
    the env allowlist, that can't be resolved from settings alone.
    """
    settings = get_settings()
    granted_admin_ids = await uow.admin_grants.list_active_telegram_ids()
    is_admin = is_superadmin_id(telegram_id, settings, granted_admin_ids)
    return main_menu_keyboard(language, is_admin=is_admin)


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
