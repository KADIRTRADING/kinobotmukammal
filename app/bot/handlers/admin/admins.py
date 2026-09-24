"""Admin "👑 Admins" section: lets an OWNER (a Telegram id listed in the
`TELEGRAM_SUPERADMIN_IDS` env var) grant or revoke in-Telegram admin-panel
access for other Telegram accounts at RUNTIME -- no `.env` edit, no
process restart.

Security model (see also `app.core.admin_access` module docstring):
  - Every handler in this file that MUTATES the `admin_grants` table
    (`handle_admins_add_start` onward, `handle_admin_revoke_prompt`,
    `handle_admin_revoke_confirm`) explicitly re-checks
    `is_owner_admin(user.telegram_id, settings)` INSIDE the handler body,
    on top of the router-level `AdminAccessFilter` that already covers
    this whole admin subtree. This is deliberate defense-in-depth: the
    outer filter only proves "this sender is SOME kind of admin (owner OR
    granted)" -- it does NOT distinguish tiers. Without this per-handler
    check, a granted (non-owner) admin who reaches this section via the
    menu button would be able to grant themselves further admins or
    revoke the owner, which would break the one-directional trust model
    the whole feature depends on.
  - Read-only actions (`handle_admins_menu`, `handle_admins_list`) are
    safe to show to any authorized admin; the keyboards conditionally
    hide mutating buttons for non-owners (see `admin_admins_menu_keyboard`,
    `admin_admins_list_keyboard`), but that hiding is a UX nicety only --
    the real boundary is the `is_owner_admin` checks below.
  - A granted admin can NEVER grant/revoke access for themselves or
    anyone else, including revoking their OWN access -- only an owner can
    do either. This means a compromised granted-admin account cannot
    entrench itself or add more admins of its own.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_admins import (
    admin_admins_grant_confirm_keyboard,
    admin_admins_list_keyboard,
    admin_admins_menu_keyboard,
    admin_admins_revoke_confirm_keyboard,
)
from app.bot.keyboards.admin_common import admin_back_row
from app.bot.states import AdminAdminsStates
from app.config import get_settings
from app.core.admin_access import is_owner_admin
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.admin_management_service import AdminManagementService

router = Router(name="admin_admins")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:admins")
async def handle_admins_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    is_owner = is_owner_admin(user.telegram_id, get_settings())
    await callback.message.edit_text(
        t(user.language, "admin_admins_menu_title"),
        reply_markup=admin_admins_menu_keyboard(user.language, is_owner=is_owner),
    )
    await callback.answer()


@router.callback_query(F.data == "aa:list")
async def handle_admins_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    settings = get_settings()
    is_owner = is_owner_admin(user.telegram_id, settings)

    owner_lines = [
        t(user.language, "admin_admins_owner_line", telegram_id=owner_id)
        for owner_id in sorted(settings.telegram_superadmin_ids)
    ]
    grants = await AdminManagementService(uow).list_grants(active_only=True)
    granted_lines = [
        t(
            user.language,
            "admin_admins_granted_line",
            telegram_id=g.telegram_id,
            label=_esc(g.label) if g.label else "—",
            granted_by=g.granted_by_telegram_id,
        )
        for g in grants
    ]

    body_parts = [t(user.language, "admin_admins_owners_header")]
    body_parts.extend(owner_lines or [t(user.language, "admin_admins_none")])
    body_parts.append("")
    body_parts.append(t(user.language, "admin_admins_granted_header"))
    body_parts.extend(granted_lines or [t(user.language, "admin_admins_none")])

    await callback.message.edit_text(
        "\n".join(body_parts),
        reply_markup=admin_admins_list_keyboard(grants, user.language, is_owner=is_owner),
    )
    await callback.answer()


# --- Grant a new admin (owners only) ----------------------------------------------


@router.callback_query(F.data == "aa:add")
async def handle_admins_add_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    if not is_owner_admin(user.telegram_id, get_settings()):
        # A granted (non-owner) admin somehow reaching this callback (e.g.
        # a stale keyboard from before a revocation) -- reject silently
        # from their perspective, loudly in the audit log.
        await record_admin_action(
            uow,
            user,
            action="admins_add_denied_not_owner",
            entity_type="admin_grant",
        )
        await callback.answer(t(user.language, "admin_admins_owners_only"), show_alert=True)
        return

    await state.set_state(AdminAdminsStates.awaiting_grant_telegram_id)
    await callback.message.edit_text(
        t(user.language, "admin_admins_enter_telegram_id_prompt"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:admins")]
        ),
    )
    await callback.answer()


@router.message(StateFilter(AdminAdminsStates.awaiting_grant_telegram_id), F.text)
async def handle_admins_grant_telegram_id_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    settings = get_settings()
    if not is_owner_admin(user.telegram_id, settings):
        await state.clear()
        await message.answer(t(user.language, "admin_admins_owners_only"))
        return

    raw = message.text.strip()
    if not raw.isdigit():
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    target_id = int(raw)

    if target_id == user.telegram_id:
        await message.answer(t(user.language, "admin_admins_cannot_self_grant"))
        return
    if target_id in settings.telegram_superadmin_ids:
        await message.answer(t(user.language, "admin_admins_already_owner"))
        return
    existing = await uow.admin_grants.get_by_telegram_id(target_id)
    if existing is not None and existing.is_active:
        await message.answer(t(user.language, "admin_admins_already_granted"))
        return

    await state.update_data(grant_telegram_id=target_id)
    await state.set_state(AdminAdminsStates.awaiting_grant_label)
    await message.answer(t(user.language, "admin_admins_enter_label_prompt"))


@router.message(StateFilter(AdminAdminsStates.awaiting_grant_label), F.text)
async def handle_admins_grant_label_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    if not is_owner_admin(user.telegram_id, get_settings()):
        await state.clear()
        await message.answer(t(user.language, "admin_admins_owners_only"))
        return

    value = message.text.strip()
    label = None if value == "-" else value
    await state.update_data(grant_label=label)
    data = await state.get_data()
    await message.answer(
        t(
            user.language,
            "admin_admins_grant_confirm_prompt",
            telegram_id=data["grant_telegram_id"],
            label=_esc(label) if label else "—",
        ),
        reply_markup=admin_admins_grant_confirm_keyboard(user.language),
    )


@router.callback_query(
    StateFilter(AdminAdminsStates.awaiting_grant_label), F.data == "aa:grant_confirm"
)
async def handle_admins_grant_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    if not is_owner_admin(user.telegram_id, get_settings()):
        await state.clear()
        await callback.answer(t(user.language, "admin_admins_owners_only"), show_alert=True)
        return

    data = await state.get_data()
    target_id = data["grant_telegram_id"]
    label = data.get("grant_label")

    grant = await AdminManagementService(uow).grant(
        telegram_id=target_id, granted_by_telegram_id=user.telegram_id, label=label
    )
    await record_admin_action(
        uow,
        user,
        action="grant_admin_access",
        entity_type="admin_grant",
        entity_id=str(target_id),
        after={"telegram_id": target_id, "label": label},
    )
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_admins_granted", telegram_id=grant.telegram_id),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:admins")]
        ),
    )
    await callback.answer()

    # Best-effort notification to the newly granted admin -- never fatal if
    # they've blocked the bot or never started it.
    try:
        await callback.bot.send_message(
            chat_id=target_id, text=t(user.language, "admin_admins_you_were_granted")
        )
    except Exception:
        pass


# --- Revoke an existing admin (owners only) ---------------------------------------


@router.callback_query(F.data.startswith("aa:revoke:"))
async def handle_admin_revoke_prompt(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    if not is_owner_admin(user.telegram_id, get_settings()):
        await record_admin_action(
            uow,
            user,
            action="admins_revoke_denied_not_owner",
            entity_type="admin_grant",
        )
        await callback.answer(t(user.language, "admin_admins_owners_only"), show_alert=True)
        return

    target_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        t(user.language, "admin_admins_revoke_confirm_prompt", telegram_id=target_id),
        reply_markup=admin_admins_revoke_confirm_keyboard(target_id, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("aa:revoke_confirm:"))
async def handle_admin_revoke_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    if not is_owner_admin(user.telegram_id, get_settings()):
        await record_admin_action(
            uow,
            user,
            action="admins_revoke_denied_not_owner",
            entity_type="admin_grant",
        )
        await callback.answer(t(user.language, "admin_admins_owners_only"), show_alert=True)
        return

    target_id = int(callback.data.split(":")[2])
    grant = await AdminManagementService(uow).revoke(
        target_id, revoked_by_telegram_id=user.telegram_id
    )
    if grant is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return

    await record_admin_action(
        uow,
        user,
        action="revoke_admin_access",
        entity_type="admin_grant",
        entity_id=str(target_id),
        before={"telegram_id": target_id, "label": grant.label},
    )
    await callback.message.edit_text(
        t(user.language, "admin_admins_revoked", telegram_id=target_id),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:admins")]
        ),
    )
    await callback.answer()

    try:
        await callback.bot.send_message(
            chat_id=target_id, text=t(user.language, "admin_admins_you_were_revoked")
        )
    except Exception:
        pass
