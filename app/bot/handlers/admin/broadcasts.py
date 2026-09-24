"""Admin Broadcasts section: compose text (uz/ru/en) or a photo+caption,
preview the exact content and an estimated recipient count, confirm, and
queue -- never send inline. Progress and cancellation are surfaced from
`Broadcast.sent_count/failed_count/skipped_count/total_recipients`, which
`app.workers.broadcast_worker` updates as it drains the queue.

Duplicate-send avoidance: `BroadcastService.enqueue` snapshots the
recipient list into `broadcast_recipients` ONCE at confirm time (with a
unique constraint on (broadcast_id, user_id)), and the worker only ever
sends to PENDING recipients, marking each SENT/FAILED/SKIPPED as it goes --
so re-opening this admin screen or the worker restarting can never cause a
second send to the same recipient for the same broadcast.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_broadcasts import (
    admin_broadcast_active_list_keyboard,
    admin_broadcast_confirm_keyboard,
    admin_broadcast_target_keyboard,
    admin_broadcasts_menu_keyboard,
)
from app.bot.keyboards.admin_common import admin_back_row
from app.bot.states import AdminBroadcastStates
from app.db.models.enums import BroadcastStatus, BroadcastTarget
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.broadcast_service import BroadcastService

router = Router(name="admin_broadcasts")

_TARGET_LABEL_KEYS = {
    BroadcastTarget.ALL.value: "admin_broadcast_target_all_button",
    BroadcastTarget.PREMIUM.value: "admin_broadcast_target_premium_button",
    BroadcastTarget.FREE.value: "admin_broadcast_target_free_button",
}


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:bcast")
async def handle_broadcasts_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_broadcasts_menu_title"),
        reply_markup=admin_broadcasts_menu_keyboard(user.language),
    )
    await callback.answer()


# --- Compose ------------------------------------------------------------------


@router.callback_query(F.data == "abc:create")
async def handle_broadcast_create_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(AdminBroadcastStates.choosing_target)
    await callback.message.edit_text(
        t(user.language, "admin_broadcast_choose_target_prompt"),
        reply_markup=admin_broadcast_target_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(AdminBroadcastStates.choosing_target), F.data.startswith("abc:target:")
)
async def handle_broadcast_target_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    target = callback.data.split(":")[2]
    await state.update_data(target=target)
    await state.set_state(AdminBroadcastStates.awaiting_text_uz)
    await callback.message.edit_text(t(user.language, "admin_broadcast_enter_text_uz_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminBroadcastStates.awaiting_text_uz), F.text)
async def handle_broadcast_text_uz(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(text_uz=message.text)
    await state.set_state(AdminBroadcastStates.awaiting_text_ru)
    await message.answer(t(user.language, "admin_broadcast_enter_text_ru_prompt"))


@router.message(StateFilter(AdminBroadcastStates.awaiting_text_ru), F.text)
async def handle_broadcast_text_ru(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(text_ru=message.text)
    await state.set_state(AdminBroadcastStates.awaiting_text_en)
    await message.answer(t(user.language, "admin_broadcast_enter_text_en_prompt"))


@router.message(StateFilter(AdminBroadcastStates.awaiting_text_en), F.text)
async def handle_broadcast_text_en(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(text_en=message.text)
    await state.set_state(AdminBroadcastStates.awaiting_photo)
    await message.answer(t(user.language, "admin_broadcast_add_photo_prompt"))


@router.message(StateFilter(AdminBroadcastStates.awaiting_photo))
async def handle_broadcast_photo(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip() != "-":
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(AdminBroadcastStates.confirming)

    data = await state.get_data()
    estimate = await _estimate_recipients(uow, data["target"])
    target_label = t(
        user.language, _TARGET_LABEL_KEYS.get(data["target"], "admin_broadcast_target_all_button")
    )

    preview_text = t(
        user.language,
        "admin_broadcast_preview_title",
        target_label=target_label,
        recipient_count=estimate,
        text_uz=_esc(data["text_uz"]),
        text_ru=_esc(data["text_ru"]),
        text_en=_esc(data["text_en"]),
    )
    if photo_file_id:
        await message.answer_photo(
            photo=photo_file_id,
            caption=preview_text,
            reply_markup=admin_broadcast_confirm_keyboard(user.language),
        )
    else:
        await message.answer(
            preview_text, reply_markup=admin_broadcast_confirm_keyboard(user.language)
        )


async def _estimate_recipients(uow: UnitOfWork, target: str) -> int:
    if target == BroadcastTarget.PREMIUM.value:
        users = await uow.users.iter_broadcast_targets(premium_only=True)
    elif target == BroadcastTarget.FREE.value:
        users = await uow.users.iter_broadcast_targets(premium_only=False)
    else:
        users = await uow.users.iter_broadcast_targets()
    return len(users)


@router.callback_query(StateFilter(AdminBroadcastStates.confirming), F.data == "abc:cancel_compose")
async def handle_broadcast_cancel_compose(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_action_cancelled"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:bcast")]
        ),
    )
    await callback.answer()


@router.callback_query(StateFilter(AdminBroadcastStates.confirming), F.data == "abc:send")
async def handle_broadcast_send_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    broadcast_service = BroadcastService(uow)
    broadcast = await broadcast_service.create_draft(
        admin_id=user.id,
        target=BroadcastTarget(data["target"]),
        text_uz=data["text_uz"],
        text_ru=data["text_ru"],
        text_en=data["text_en"],
        photo_file_id=data.get("photo_file_id"),
    )
    recipient_count = await broadcast_service.enqueue(broadcast)
    await record_admin_action(
        uow,
        user,
        action="create_broadcast",
        entity_type="broadcast",
        entity_id=str(broadcast.id),
        after={"target": data["target"], "recipients": recipient_count},
    )
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_broadcast_queued", count=recipient_count),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:bcast")]
        ),
    )
    await callback.answer()


# --- Active / progress ------------------------------------------------------------


@router.callback_query(F.data == "abc:active")
async def handle_broadcast_active_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    active = await uow.broadcasts.list_queued_or_running()
    if not active:
        await callback.message.edit_text(
            t(user.language, "admin_broadcast_active_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, "adm:bcast")]
            ),
        )
        await callback.answer()
        return
    lines = [
        t(
            user.language,
            "admin_broadcast_progress_item",
            id=b.id,
            status=b.status,
            sent=b.sent_count,
            total=b.total_recipients,
            failed=b.failed_count,
            skipped=b.skipped_count,
        )
        for b in active
    ]
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=admin_broadcast_active_list_keyboard(active, user.language)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("abc:view:"))
async def handle_broadcast_view(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    broadcast_id = int(callback.data.split(":")[2])
    broadcast = await uow.broadcasts.get(broadcast_id)
    if broadcast is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await callback.answer(
        t(
            user.language,
            "admin_broadcast_progress_item",
            id=broadcast.id,
            status=broadcast.status,
            sent=broadcast.sent_count,
            total=broadcast.total_recipients,
            failed=broadcast.failed_count,
            skipped=broadcast.skipped_count,
        ),
        show_alert=True,
    )


@router.callback_query(F.data.startswith("abc:cancelrun:"))
async def handle_broadcast_cancel_running(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    broadcast_id = int(callback.data.split(":")[2])
    broadcast = await uow.broadcasts.get(broadcast_id)
    if broadcast is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    if broadcast.status not in (BroadcastStatus.QUEUED.value, BroadcastStatus.RUNNING.value):
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await BroadcastService(uow).cancel(broadcast)
    await record_admin_action(
        uow, user, action="cancel_broadcast", entity_type="broadcast", entity_id=str(broadcast_id)
    )
    await callback.answer(
        t(user.language, "admin_broadcast_cancelled", id=broadcast_id), show_alert=True
    )
    await handle_broadcast_active_list(callback, uow, user, **kwargs)
