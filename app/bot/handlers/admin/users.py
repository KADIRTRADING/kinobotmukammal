"""Admin Users section: search by Telegram ID or username, view status and
purchase history, block/unblock, grant/revoke premium, and adjust gift
balance with a mandatory reason.

Every balance/premium mutation reuses `GiftService`/`WalletService`/
`EntitlementService` -- the exact same code paths used by user-facing gift
and purchase flows -- so admin grants obey the same ledger/entitlement
invariants (idempotency, no negative balances, exactly-once entitlement)
as everything else in the bot.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_common import admin_back_row, paginate
from app.bot.keyboards.admin_users import (
    admin_user_detail_keyboard,
    admin_user_orders_keyboard,
    admin_user_plan_pick_keyboard,
    admin_user_search_results_keyboard,
)
from app.bot.states import AdminUserStates
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.entitlement_service import EntitlementService
from app.services.gift_service import GiftService
from app.services.money import InsufficientFundsError
from app.services.wallet_service import WalletService

router = Router(name="admin_users")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


def _user_label(target: User) -> str:
    return f"@{target.username}" if target.username else str(target.telegram_id)


@router.callback_query(F.data == "adm:users")
async def handle_users_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await state.set_state(AdminUserStates.awaiting_search_query)
    await callback.message.edit_text(
        t(user.language, "admin_users_menu_title"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[admin_back_row(user.language)]),
    )
    await callback.answer()


@router.message(StateFilter(AdminUserStates.awaiting_search_query), F.text)
async def handle_user_search_query(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    query = message.text.strip()
    results = await uow.users.search_by_name_or_id(query, limit=1000)
    await state.clear()
    if not results:
        await message.answer(
            t(user.language, "admin_users_search_empty"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[admin_back_row(user.language)]),
        )
        return
    page_items, total_pages = paginate(results, 0)
    await message.answer(
        (
            t(user.language, "admin_users_search_empty")
            if not page_items
            else t(user.language, "admin_users_menu_title")
        ),
        reply_markup=admin_user_search_results_keyboard(page_items, user.language, 0, total_pages),
    )


@router.callback_query(F.data.startswith("au:view:"))
async def handle_user_view(callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs) -> None:
    user_id = int(callback.data.split(":")[2])
    target = await uow.users.get_by_id(user_id)
    if target is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return

    balances = await WalletService(uow).get_balances(target.id)
    balances_str = ", ".join(f"{cur}: {b['available']}" for cur, b in balances.items()) or "—"
    orders_count = await uow.orders.count_for_user(target.id)
    status = "🚫 " + _esc(target.block_reason or "") if target.is_blocked else "✅"

    await callback.message.edit_text(
        t(
            user.language,
            "admin_user_detail_title",
            label=_esc(_user_label(target)),
            telegram_id=target.telegram_id,
            target_language=target.language,
            status=status,
            premium_until=target.premium_until.isoformat() if target.premium_until else "—",
            referral_code=_esc(target.referral_code),
            orders_count=orders_count,
            balances=_esc(balances_str),
        ),
        reply_markup=admin_user_detail_keyboard(target, user.language),
    )
    await callback.answer()


# --- Block / unblock -----------------------------------------------------------


@router.callback_query(F.data.startswith("au:block:"))
async def handle_user_block_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    user_id = int(callback.data.split(":")[2])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminUserStates.awaiting_block_reason)
    await callback.message.edit_text(t(user.language, "admin_user_block_reason_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminUserStates.awaiting_block_reason), F.text)
async def handle_user_block_reason(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    target = await uow.users.get_by_id(data["target_user_id"])
    if target is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    reason = message.text.strip()
    await uow.users.set_blocked(target, True, reason)
    await record_admin_action(
        uow,
        user,
        action="block_user",
        entity_type="user",
        entity_id=str(target.id),
        note=reason,
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_user_blocked"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"au:view:{target.id}")]
        ),
    )


@router.callback_query(F.data.startswith("au:unblock:"))
async def handle_user_unblock(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    user_id = int(callback.data.split(":")[2])
    target = await uow.users.get_by_id(user_id)
    if target is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await uow.users.set_blocked(target, False)
    await record_admin_action(
        uow, user, action="unblock_user", entity_type="user", entity_id=str(target.id)
    )
    await callback.answer(t(user.language, "admin_user_unblocked"), show_alert=True)
    await handle_user_view(callback, uow, user, **kwargs)


# --- Grant / revoke premium ------------------------------------------------------


@router.callback_query(F.data.startswith("au:grant:"))
async def handle_user_grant_premium_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    user_id = int(callback.data.split(":")[2])
    plans = await uow.plans.list_active()
    if not plans:
        await callback.answer(t(user.language, "admin_no_items"), show_alert=True)
        return
    await callback.message.edit_text(
        t(user.language, "admin_user_choose_plan_prompt"),
        reply_markup=admin_user_plan_pick_keyboard(plans, user_id, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("au:grantplan:"))
async def handle_user_grant_premium_plan_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    _, _, user_id_str, plan_id_str = callback.data.split(":")
    await state.update_data(target_user_id=int(user_id_str), grant_plan_id=int(plan_id_str))
    await state.set_state(AdminUserStates.awaiting_grant_premium_reason)
    await callback.message.edit_text(t(user.language, "admin_user_grant_premium_reason_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminUserStates.awaiting_grant_premium_reason), F.text)
async def handle_user_grant_premium_reason(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    target = await uow.users.get_by_id(data["target_user_id"])
    plan = await uow.plans.get(data["grant_plan_id"])
    if target is None or plan is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    reason = message.text.strip()

    gift = await GiftService(uow).admin_gift_premium(
        admin_id=user.id, recipient_user_id=target.id, plan_id=plan.id, reason=reason
    )
    await record_admin_action(
        uow,
        user,
        action="grant_premium",
        entity_type="user",
        entity_id=str(target.id),
        after={"plan_id": plan.id, "gift_id": gift.id},
        note=reason,
    )
    await state.clear()
    refreshed = await uow.users.get_by_id(target.id)
    until_str = (
        refreshed.premium_until.isoformat() if refreshed and refreshed.premium_until else "—"
    )
    await message.answer(
        t(
            user.language,
            "admin_user_premium_granted",
            label=_esc(_user_label(target)),
            until=until_str,
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"au:view:{target.id}")]
        ),
    )


@router.callback_query(F.data.startswith("au:revoke:"))
async def handle_user_revoke_premium(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    user_id = int(callback.data.split(":")[2])
    target = await uow.users.get_by_id(user_id)
    if target is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    if not target.is_premium_active:
        await callback.answer(t(user.language, "admin_user_no_active_premium"), show_alert=True)
        return
    await EntitlementService(uow).revoke_future(target.id)
    await record_admin_action(
        uow, user, action="revoke_premium", entity_type="user", entity_id=str(target.id)
    )
    await callback.answer(
        t(user.language, "admin_user_premium_revoked", label=_user_label(target)), show_alert=True
    )
    await handle_user_view(callback, uow, user, **kwargs)


# --- Gift balance (mandatory reason) --------------------------------------------


@router.callback_query(F.data.startswith("au:gift:"))
async def handle_user_gift_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    user_id = int(callback.data.split(":")[2])
    await state.update_data(target_user_id=user_id)
    await state.set_state(AdminUserStates.awaiting_gift_amount)
    await callback.message.edit_text(t(user.language, "admin_user_enter_gift_amount_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminUserStates.awaiting_gift_amount), F.text)
async def handle_user_gift_amount(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    if amount <= 0:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(gift_amount=amount)
    await state.set_state(AdminUserStates.awaiting_gift_currency)
    await message.answer(t(user.language, "admin_user_enter_gift_currency_prompt"))


@router.message(StateFilter(AdminUserStates.awaiting_gift_currency), F.text)
async def handle_user_gift_currency(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    currency = message.text.strip().upper()
    if not (2 <= len(currency) <= 8):
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(gift_currency=currency)
    await state.set_state(AdminUserStates.awaiting_gift_reason)
    await message.answer(t(user.language, "admin_user_enter_gift_reason_prompt"))


@router.message(StateFilter(AdminUserStates.awaiting_gift_reason), F.text)
async def handle_user_gift_reason(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    reason = message.text.strip()
    if not reason:
        await message.answer(t(user.language, "admin_user_gift_reason_required"))
        return
    data = await state.get_data()
    target = await uow.users.get_by_id(data["target_user_id"])
    if target is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return

    amount = data["gift_amount"]
    currency = data["gift_currency"]

    try:
        await GiftService(uow).admin_gift_balance(
            admin_id=user.id,
            recipient_user_id=target.id,
            currency=currency,
            amount=amount,
            reason=reason,
        )
    except InsufficientFundsError:
        # Admin gifts CREDIT the recipient and never debit anyone, so this
        # branch should be unreachable in practice; kept for defense-in-depth.
        await message.answer(t(user.language, "error_generic"))
        await state.clear()
        return

    await record_admin_action(
        uow,
        user,
        action="gift_balance",
        entity_type="user",
        entity_id=str(target.id),
        after={"amount": amount, "currency": currency},
        note=reason,
    )
    await state.clear()
    await message.answer(
        t(
            user.language,
            "admin_user_gift_given",
            amount=amount,
            currency=currency,
            label=_esc(_user_label(target)),
        ),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"au:view:{target.id}")]
        ),
    )


# --- Order history ---------------------------------------------------------------


@router.callback_query(F.data.startswith("au:orders:"))
async def handle_user_orders(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    _, _, user_id_str, page_str = callback.data.split(":")
    user_id, page = int(user_id_str), int(page_str)
    target = await uow.users.get_by_id(user_id)
    if target is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return

    total = await uow.orders.count_for_user(user_id)
    if total == 0:
        await callback.message.edit_text(
            t(user.language, "admin_user_orders_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, f"au:view:{user_id}")]
            ),
        )
        await callback.answer()
        return

    page_size = 8
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    orders = await uow.orders.list_for_user(user_id, limit=page_size, offset=page * page_size)

    lines = [
        t(
            user.language,
            "admin_user_order_line",
            uid=str(o.uid)[:8],
            amount=o.net_amount,
            currency=o.currency,
            status=o.status,
            date=o.created_at.strftime("%Y-%m-%d"),
        )
        for o in orders
    ]
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_user_orders_keyboard(user_id, user.language, page, total_pages),
    )
    await callback.answer()
