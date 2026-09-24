"""Admin Settings & Audit section: shows the bot's global runtime settings
(referral commission on renewals, blogger reward rate, promo stacking),
lets the admin flip the safe boolean toggles, and displays the recent
admin action audit log.

Every toggle reuses `SettingsService` (app/services/settings_service.py)
-- the same key/value settings table `PurchaseService`/`BloggerRewardService`
read from -- so a change here takes effect immediately and consistently
everywhere else in the bot.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_common import admin_back_row, paginate
from app.bot.keyboards.admin_settings import admin_audit_menu_keyboard, admin_settings_menu_keyboard
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.settings_service import SettingsService

router = Router(name="admin_settings")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:settings")
async def handle_settings_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await _render_settings(callback, uow, user)


async def _render_settings(callback: CallbackQuery, uow: UnitOfWork, user: User) -> None:
    settings_service = SettingsService(uow)
    renewals = await settings_service.referral_commission_on_renewals()
    stacking = await settings_service.promo_stacking_allowed()
    rate, currency = await settings_service.global_blogger_reward_per_1000()

    renewals_label = "✅" if renewals else "⛔"
    stacking_label = "✅" if stacking else "⛔"

    await callback.message.edit_text(
        t(
            user.language,
            "admin_settings_current_title",
            renewals=renewals_label,
            reward_rate=rate,
            reward_currency=_esc(currency),
            stacking=stacking_label,
        ),
        reply_markup=admin_settings_menu_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(F.data == "as:toggle_renewals")
async def handle_toggle_renewals(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    settings_service = SettingsService(uow)
    current = await settings_service.referral_commission_on_renewals()
    new_value = not current
    await settings_service.set_referral_commission_on_renewals(new_value)
    await record_admin_action(
        uow,
        user,
        action="toggle_referral_commission_on_renewals",
        entity_type="settings",
        after={"enabled": new_value},
    )
    key = "admin_settings_renewals_enabled" if new_value else "admin_settings_renewals_disabled"
    await callback.answer(t(user.language, key), show_alert=True)
    await _render_settings(callback, uow, user)


@router.callback_query(F.data == "as:toggle_stacking")
async def handle_toggle_stacking(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    settings_service = SettingsService(uow)
    current = await settings_service.promo_stacking_allowed()
    new_value = not current
    await settings_service.set_promo_stacking_allowed(new_value)
    await record_admin_action(
        uow,
        user,
        action="toggle_promo_stacking",
        entity_type="settings",
        after={"enabled": new_value},
    )
    key = "admin_settings_stacking_enabled" if new_value else "admin_settings_stacking_disabled"
    await callback.answer(t(user.language, key), show_alert=True)
    await _render_settings(callback, uow, user)


# --- Audit log ----------------------------------------------------------------


@router.callback_query(F.data == "adm:audit")
async def handle_audit_menu(callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs) -> None:
    logs = await uow.audit.list_recent(limit=50)
    if not logs:
        await callback.message.edit_text(
            t(user.language, "admin_audit_empty"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[admin_back_row(user.language)]),
        )
        await callback.answer()
        return
    page_items, _total_pages = paginate(logs, 0, page_size=15)
    lines = [
        t(
            user.language,
            "admin_audit_entry_line",
            date=log.created_at.strftime("%Y-%m-%d %H:%M"),
            admin=_esc(log.admin_username),
            action=_esc(log.action),
            entity=f"{log.entity_type}#{log.entity_id}" if log.entity_id else log.entity_type,
        )
        for log in page_items
    ]
    await callback.message.edit_text(
        t(user.language, "admin_audit_menu_title") + "\n\n" + "\n".join(lines),
        reply_markup=admin_audit_menu_keyboard(user.language),
    )
    await callback.answer()
