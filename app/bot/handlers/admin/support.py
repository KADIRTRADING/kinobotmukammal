"""Admin Support section: list open tickets, read the full message thread,
reply through the bot (delivered to the user's own chat), and close.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_common import admin_back_row, paginate
from app.bot.keyboards.admin_support import (
    admin_support_list_keyboard,
    admin_support_ticket_keyboard,
)
from app.bot.states import AdminSupportStates
from app.db.models.enums import SupportSenderType
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t

router = Router(name="admin_support")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:support")
async def handle_support_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await _render_ticket_list(callback, uow, user, page=0)


@router.callback_query(F.data.startswith("asu:list:"))
async def handle_support_list_page(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    page = int(callback.data.split(":")[2])
    await _render_ticket_list(callback, uow, user, page=page)


async def _render_ticket_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, *, page: int
) -> None:
    tickets = await uow.support.list_open(limit=1000)
    if not tickets:
        await callback.message.edit_text(
            t(user.language, "admin_support_empty"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[admin_back_row(user.language)]),
        )
        await callback.answer()
        return
    page_items, total_pages = paginate(tickets, page)
    lines = []
    for tk in page_items:
        requester = await uow.users.get_by_id(tk.user_id)
        label = f"@{requester.username}" if requester and requester.username else str(tk.user_id)
        lines.append(
            t(
                user.language,
                "admin_support_ticket_item",
                ticket_id=tk.id,
                label=_esc(label),
                subject=_esc(tk.subject),
            )
        )
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_support_list_keyboard(page_items, user.language, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("asu:view:"))
async def handle_support_ticket_view(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    ticket_id = int(callback.data.split(":")[2])
    ticket = await uow.support.get_ticket(ticket_id)
    if ticket is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    requester = await uow.users.get_by_id(ticket.user_id)
    label = f"@{requester.username}" if requester and requester.username else str(ticket.user_id)

    messages = await uow.support.list_messages(ticket_id, limit=50)
    lines = [
        t(
            user.language,
            "admin_support_message_line",
            date=m.created_at.strftime("%Y-%m-%d %H:%M"),
            sender=m.sender_type,
            text=_esc(m.text),
        )
        for m in messages
    ]
    await callback.message.edit_text(
        t(
            user.language,
            "admin_support_ticket_detail",
            ticket_id=ticket.id,
            label=_esc(label),
            messages="\n".join(lines) or "—",
        ),
        reply_markup=admin_support_ticket_keyboard(ticket.id, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("asu:reply:"))
async def handle_support_reply_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    ticket_id = int(callback.data.split(":")[2])
    await state.update_data(ticket_id=ticket_id)
    await state.set_state(AdminSupportStates.awaiting_reply_text)
    await callback.message.edit_text(t(user.language, "admin_support_reply_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminSupportStates.awaiting_reply_text), F.text)
async def handle_support_reply_text(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    ticket = await uow.support.get_ticket(data["ticket_id"])
    if ticket is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    reply_text = message.text.strip()

    await uow.support.add_message(
        ticket_id=ticket.id, sender_type=SupportSenderType.ADMIN, sender_id=user.id, text=reply_text
    )
    await record_admin_action(
        uow,
        user,
        action="reply_support_ticket",
        entity_type="support_ticket",
        entity_id=str(ticket.id),
    )

    requester = await uow.users.get_by_id(ticket.user_id)
    if requester is not None:
        try:
            await message.bot.send_message(
                chat_id=requester.telegram_id,
                text=t(requester.language, "support_ticket_reply_notice", text=reply_text),
            )
        except Exception:
            pass

    await state.clear()
    await message.answer(
        t(user.language, "admin_support_reply_sent"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"asu:view:{ticket.id}")]
        ),
    )


@router.callback_query(F.data.startswith("asu:close:"))
async def handle_support_close(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    ticket_id = int(callback.data.split(":")[2])
    ticket = await uow.support.get_ticket(ticket_id)
    if ticket is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await uow.support.close_ticket(ticket)
    await record_admin_action(
        uow,
        user,
        action="close_support_ticket",
        entity_type="support_ticket",
        entity_id=str(ticket_id),
    )
    await callback.answer(
        t(user.language, "admin_support_ticket_closed", ticket_id=ticket_id), show_alert=True
    )
    await _render_ticket_list(callback, uow, user, page=0)
