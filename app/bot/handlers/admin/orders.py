"""Admin Orders/Payments section: list and filter orders, inspect payment
status and raw provider events, and record a REFUND as the only supported
manual write action -- always with an explicit confirmation step.

Critical invariant (spec): an order is NEVER marked "paid" by an admin
button. The only way an order transitions to PAID is
`PurchaseService.confirm_payment`, called exclusively from the real
payment webhooks (`app/api/webhooks/*`) and the Telegram Stars
`successful_payment` handler -- i.e. from an authenticated provider update,
never from this admin UI. This screen is read-only for the PAID
transition; the only mutation exposed here is `refund_order` on an
ALREADY-paid order, which is the same service the automated Stripe/Click
refund webhooks use.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_common import admin_back_row
from app.bot.keyboards.admin_orders import (
    admin_order_detail_keyboard,
    admin_order_list_keyboard,
    admin_order_refund_confirm_keyboard,
    admin_orders_menu_keyboard,
    admin_orders_status_filter_keyboard,
)
from app.bot.states import AdminOrderStates
from app.db.models.enums import OrderStatus
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.purchase_service import PurchaseService

router = Router(name="admin_orders")

PAGE_SIZE = 8


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:orders")
async def handle_orders_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_orders_menu_title"),
        reply_markup=admin_orders_menu_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(F.data == "ao:filter")
async def handle_orders_filter_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    await callback.message.edit_text(
        t(user.language, "admin_orders_choose_status_prompt"),
        reply_markup=admin_orders_status_filter_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ao:list:"))
async def handle_orders_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    page = int(callback.data.split(":")[2])
    await _render_order_list(callback, uow, user, page=page, status=None)


@router.callback_query(F.data.startswith("ao:list_status:"))
async def handle_orders_list_by_status(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    _, _, status, page_str = callback.data.split(":")
    await _render_order_list(callback, uow, user, page=int(page_str), status=status)


async def _render_order_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, *, page: int, status: str | None
) -> None:
    total = await uow.orders.count_recent(status=status)
    if total == 0:
        await callback.message.edit_text(
            t(user.language, "admin_orders_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, "adm:orders")]
            ),
        )
        await callback.answer()
        return

    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    orders = await uow.orders.list_recent(limit=PAGE_SIZE, offset=page * PAGE_SIZE, status=status)

    lines = [
        t(
            user.language,
            "admin_order_list_item",
            uid=str(o.uid)[:8],
            amount=o.net_amount,
            currency=o.currency,
            provider=o.provider_code,
            status=o.status,
        )
        for o in orders
    ]
    prefix = f"ao:list_status:{status}:" if status else "ao:list:"
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_order_list_keyboard(
            orders, user.language, page, total_pages, prefix=prefix
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ao:view:"))
async def handle_order_view(callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs) -> None:
    order_id = int(callback.data.split(":")[2])
    order = await uow.orders.get(order_id)
    if order is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    buyer = await uow.users.get_by_id(order.buyer_user_id)
    buyer_label = f"@{buyer.username}" if buyer and buyer.username else str(order.buyer_user_id)
    plan = await uow.plans.get(order.plan_id) if order.plan_id else None

    await callback.message.edit_text(
        t(
            user.language,
            "admin_order_detail_title",
            uid=str(order.uid),
            buyer=_esc(buyer_label),
            plan=_esc(plan.code) if plan else "—",
            amount=order.net_amount,
            currency=order.currency,
            provider=order.provider_code,
            status=order.status,
            created_at=order.created_at.strftime("%Y-%m-%d %H:%M"),
            paid_at=order.paid_at.strftime("%Y-%m-%d %H:%M") if order.paid_at else "—",
            provider_reference=_esc(order.provider_reference),
        ),
        reply_markup=admin_order_detail_keyboard(order, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ao:events:"))
async def handle_order_provider_events(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    order_id = int(callback.data.split(":")[2])
    events = await uow.orders.list_provider_events_for_order(order_id, limit=50)
    if not events:
        await callback.answer(
            t(user.language, "admin_order_provider_events_empty"), show_alert=True
        )
        return
    lines = [
        t(
            user.language,
            "admin_order_provider_event_line",
            date=e.received_at.strftime("%Y-%m-%d %H:%M"),
            event_type=e.event_type,
            processed=e.processed,
        )
        for e in events
    ]
    await callback.message.answer("\n".join(lines))
    await callback.answer()


# --- Refund (manual, explicit confirmation, only for already-PAID orders) --------


@router.callback_query(F.data.startswith("ao:refund:"))
async def handle_order_refund_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    order_id = int(callback.data.split(":")[2])
    order = await uow.orders.get(order_id)
    if order is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    if order.status != OrderStatus.PAID.value:
        await callback.answer(t(user.language, "admin_order_cannot_refund"), show_alert=True)
        return
    await state.update_data(order_id=order_id)
    await state.set_state(AdminOrderStates.awaiting_refund_reason)
    await callback.message.edit_text(t(user.language, "admin_order_refund_reason_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminOrderStates.awaiting_refund_reason), F.text)
async def handle_order_refund_reason(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    order = await uow.orders.get(data["order_id"])
    if order is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    await state.update_data(refund_reason=message.text.strip())
    await message.answer(
        t(user.language, "admin_order_refund_confirm", uid=str(order.uid)),
        reply_markup=admin_order_refund_confirm_keyboard(order.id, user.language),
    )


@router.callback_query(
    StateFilter(AdminOrderStates.awaiting_refund_reason), F.data.startswith("ao:refund_confirm:")
)
async def handle_order_refund_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    order_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    if data.get("order_id") != order_id:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    order = await uow.orders.get(order_id)
    if order is None or order.status != OrderStatus.PAID.value:
        await state.clear()
        await callback.answer(t(user.language, "admin_order_cannot_refund"), show_alert=True)
        return

    reason = data["refund_reason"]
    await PurchaseService(uow).refund_order(order, reason=reason)
    await record_admin_action(
        uow, user, action="refund_order", entity_type="order", entity_id=str(order_id), note=reason
    )
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_order_refunded", uid=str(order.uid)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:orders")]
        ),
    )
    await callback.answer()
