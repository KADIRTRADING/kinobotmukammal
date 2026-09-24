"""Admin Mandatory Channels section: add (chat id, title, invite link),
verify the bot's own admin rights in the channel via the live Bot API,
enable/disable, and remove.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_channels import (
    admin_channel_detail_keyboard,
    admin_channel_remove_confirm_keyboard,
    admin_channels_menu_keyboard,
)
from app.bot.keyboards.admin_common import admin_back_row
from app.bot.states import AdminChannelStates
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t

router = Router(name="admin_channels")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:chans")
async def handle_channels_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    channels = await uow.catalog.list_all_channels()
    await callback.message.edit_text(
        t(user.language, "admin_channels_menu_title"),
        reply_markup=admin_channels_menu_keyboard(channels, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ah:view:"))
async def handle_channel_view(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    channel_id = int(callback.data.split(":")[2])
    channel = await uow.catalog.get_channel(channel_id)
    if channel is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    status = "✅" if channel.is_active else "⛔"
    bot_admin = "✅" if channel.bot_is_admin_verified else "⚠️"
    await callback.message.edit_text(
        t(
            user.language,
            "admin_channel_list_item",
            title=_esc(channel.title),
            chat_id=_esc(channel.chat_id),
            bot_admin=bot_admin,
            status=status,
        ),
        reply_markup=admin_channel_detail_keyboard(channel, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ah:verify:"))
async def handle_channel_verify(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    channel_id = int(callback.data.split(":")[2])
    channel = await uow.catalog.get_channel(channel_id)
    if channel is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return

    is_admin = False
    error = None
    try:
        me = await callback.bot.get_me()
        member = await callback.bot.get_chat_member(chat_id=channel.chat_id, user_id=me.id)
        is_admin = member.status in ("administrator", "creator")
    except Exception as exc:  # noqa: BLE001 -- surfaced to the admin, not swallowed
        error = str(exc)

    await uow.catalog.update_channel(channel, bot_is_admin_verified=is_admin)
    await record_admin_action(
        uow,
        user,
        action="verify_channel_admin",
        entity_type="mandatory_channel",
        entity_id=str(channel_id),
        after={"bot_is_admin_verified": is_admin, "error": error},
    )
    key = "admin_channel_verify_success" if is_admin else "admin_channel_verify_failed"
    await callback.answer(
        t(user.language, key, error=_esc(error) if error else ""), show_alert=True
    )
    await handle_channel_view(callback, uow, user, **kwargs)


@router.callback_query(F.data.startswith("ah:toggle:"))
async def handle_channel_toggle(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    channel_id = int(callback.data.split(":")[2])
    channel = await uow.catalog.get_channel(channel_id)
    if channel is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    new_state = not channel.is_active
    await uow.catalog.update_channel(channel, is_active=new_state)
    await record_admin_action(
        uow,
        user,
        action="toggle_channel",
        entity_type="mandatory_channel",
        entity_id=str(channel_id),
        after={"is_active": new_state},
    )
    key = "admin_channel_enabled" if new_state else "admin_channel_disabled"
    await callback.answer(t(user.language, key, title=channel.title), show_alert=True)
    await handle_channel_view(callback, uow, user, **kwargs)


@router.callback_query(F.data.startswith("ah:remove:"))
async def handle_channel_remove_prompt(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    channel_id = int(callback.data.split(":")[2])
    channel = await uow.catalog.get_channel(channel_id)
    if channel is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await callback.message.edit_text(
        t(user.language, "admin_channel_remove_confirm", title=_esc(channel.title)),
        reply_markup=admin_channel_remove_confirm_keyboard(channel_id, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ah:remove_confirm:"))
async def handle_channel_remove_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    channel_id = int(callback.data.split(":")[2])
    channel = await uow.catalog.get_channel(channel_id)
    if channel is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    title = channel.title
    await record_admin_action(
        uow,
        user,
        action="remove_channel",
        entity_type="mandatory_channel",
        entity_id=str(channel_id),
        before={"title": title, "chat_id": channel.chat_id},
    )
    await uow.catalog.delete_channel(channel)
    await callback.message.edit_text(
        t(user.language, "admin_channel_removed", title=_esc(title)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:chans")]
        ),
    )
    await callback.answer()


# --- Add channel ---------------------------------------------------------------


@router.callback_query(F.data == "ah:add")
async def handle_channel_add_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(AdminChannelStates.awaiting_chat_id)
    await callback.message.edit_text(
        t(user.language, "admin_channel_enter_chat_id_prompt"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:chans")]
        ),
    )
    await callback.answer()


@router.message(StateFilter(AdminChannelStates.awaiting_chat_id), F.text)
async def handle_channel_chat_id_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    chat_id = message.text.strip()
    existing = await uow.catalog.get_channel_by_chat_id(chat_id)
    if existing is not None:
        await message.answer(t(user.language, "admin_channel_chat_id_taken"))
        return
    await state.update_data(chat_id=chat_id)
    await state.set_state(AdminChannelStates.awaiting_title)
    await message.answer(t(user.language, "admin_channel_enter_title_prompt"))


@router.message(StateFilter(AdminChannelStates.awaiting_title), F.text)
async def handle_channel_title_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminChannelStates.awaiting_invite_link)
    await message.answer(t(user.language, "admin_channel_enter_invite_link_prompt"))


@router.message(StateFilter(AdminChannelStates.awaiting_invite_link), F.text)
async def handle_channel_invite_link_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    value = message.text.strip()
    invite_link = None if value == "-" else value
    data = await state.get_data()
    channel = await uow.catalog.create_channel(
        chat_id=data["chat_id"], title=data["title"], invite_link=invite_link
    )
    await record_admin_action(
        uow,
        user,
        action="create_channel",
        entity_type="mandatory_channel",
        entity_id=str(channel.id),
        after={"chat_id": channel.chat_id, "title": channel.title},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_channel_created", title=html.escape(channel.title)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:chans")]
        ),
    )
