"""Admin Promo Codes section: create bot-issued (platform-funded) codes,
review pending user/blogger-issued attribution links, approve/reject with
a reason, cancel with automatic release of unused reserve, and inspect
redemption counts.

Every mutation goes through `PromoService` (app/services/promo_service.py)
-- the same service the user-facing promo creation/redemption flow uses --
so admin actions can never bypass the funding/moderation invariants
already enforced there (e.g. `_release_all_unused` is always called on
reject/cancel).
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_common import admin_back_row, paginate
from app.bot.keyboards.admin_promos import (
    admin_promo_kind_keyboard,
    admin_promo_pending_list_keyboard,
    admin_promo_plan_pick_keyboard,
    admin_promo_review_keyboard,
    admin_promos_menu_keyboard,
)
from app.bot.states import AdminPromoStates
from app.db.models.enums import PromoKind
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.promo_service import PromoService

router = Router(name="admin_promos")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:promos")
async def handle_promos_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_promos_menu_title"),
        reply_markup=admin_promos_menu_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("apr:pending:"))
async def handle_promos_pending_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    page = int(callback.data.split(":")[2])
    pending = await uow.promos.list_pending_moderation(limit=1000)
    if not pending:
        await callback.message.edit_text(
            t(user.language, "admin_promos_pending_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, "adm:promos")]
            ),
        )
        await callback.answer()
        return
    page_items, total_pages = paginate(pending, page)
    lines = [_esc(p.code) for p in page_items]
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_promo_pending_list_keyboard(
            page_items, user.language, page, total_pages
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("apr:view:"))
async def handle_promo_review_view(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    promo_id = int(callback.data.split(":")[2])
    promo = await uow.promos.get(promo_id)
    if promo is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    issuer = await uow.users.get_by_id(promo.issuer_user_id) if promo.issuer_user_id else None
    issuer_label = (
        f"@{issuer.username}"
        if issuer and issuer.username
        else (str(issuer.telegram_id) if issuer else "bot")
    )
    attribution = promo.attribution_label or promo.attribution_url or "—"
    await callback.message.edit_text(
        t(
            user.language,
            "admin_promo_review_item",
            code=_esc(promo.code),
            issuer=_esc(issuer_label),
            attribution=_esc(attribution),
            max_uses=promo.max_uses,
        ),
        reply_markup=admin_promo_review_keyboard(promo.id, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("apr:approve:"))
async def handle_promo_approve(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    promo_id = int(callback.data.split(":")[2])
    promo = await uow.promos.get(promo_id)
    if promo is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await PromoService(uow).moderate(promo, approve=True, admin_id=user.id)
    await record_admin_action(
        uow, user, action="approve_promo", entity_type="promo_code", entity_id=str(promo_id)
    )
    await callback.answer(
        t(user.language, "admin_promo_approved", code=promo.code), show_alert=True
    )
    await callback.message.edit_text(
        t(user.language, "admin_promos_menu_title"),
        reply_markup=admin_promos_menu_keyboard(user.language),
    )


@router.callback_query(F.data.startswith("apr:reject:"))
async def handle_promo_reject_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    promo_id = int(callback.data.split(":")[2])
    await state.update_data(promo_id=promo_id)
    await state.set_state(AdminPromoStates.awaiting_reject_reason)
    await callback.message.edit_text(t(user.language, "admin_promo_reject_reason_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminPromoStates.awaiting_reject_reason), F.text)
async def handle_promo_reject_reason(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    promo = await uow.promos.get(data["promo_id"])
    if promo is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    reason = message.text.strip()
    await PromoService(uow).moderate(promo, approve=False, admin_id=user.id, reason=reason)
    await record_admin_action(
        uow,
        user,
        action="reject_promo",
        entity_type="promo_code",
        entity_id=str(promo.id),
        note=reason,
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_promo_rejected", code=_esc(promo.code)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:promos")]
        ),
    )


@router.callback_query(F.data.startswith("apr:cancel:"))
async def handle_promo_cancel_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    promo_id = int(callback.data.split(":")[2])
    await state.update_data(promo_id=promo_id)
    await state.set_state(AdminPromoStates.awaiting_cancel_reason)
    await callback.message.edit_text(t(user.language, "admin_promo_cancel_reason_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminPromoStates.awaiting_cancel_reason), F.text)
async def handle_promo_cancel_reason(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    promo = await uow.promos.get(data["promo_id"])
    if promo is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    reason = message.text.strip()
    await PromoService(uow).cancel(promo, reason=reason)
    await record_admin_action(
        uow,
        user,
        action="cancel_promo",
        entity_type="promo_code",
        entity_id=str(promo.id),
        note=reason,
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_promo_cancelled", code=_esc(promo.code)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:promos")]
        ),
    )


# --- Create bot-issued (platform-funded) code -------------------------------------


@router.callback_query(F.data == "apr:create")
async def handle_promo_create_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plans = await uow.plans.list_active()
    if not plans:
        await callback.answer(t(user.language, "admin_no_items"), show_alert=True)
        return
    await state.set_state(AdminPromoStates.choosing_plan)
    await callback.message.edit_text(
        t(user.language, "admin_promo_create_choose_plan_prompt"),
        reply_markup=admin_promo_plan_pick_keyboard(plans, user.language),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(AdminPromoStates.choosing_plan), F.data.startswith("apr:createplan:")
)
async def handle_promo_create_plan_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":")[2])
    await state.update_data(plan_id=plan_id)
    await state.set_state(AdminPromoStates.choosing_kind)
    await callback.message.edit_text(
        t(user.language, "admin_promo_create_choose_kind_prompt"),
        reply_markup=admin_promo_kind_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(AdminPromoStates.choosing_kind), F.data.startswith("apr:createkind:")
)
async def handle_promo_create_kind_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    kind = callback.data.split(":")[2]
    await state.update_data(kind=kind)
    if kind == PromoKind.PERCENT_DISCOUNT.value:
        await state.set_state(AdminPromoStates.awaiting_discount)
        await callback.message.edit_text(
            t(user.language, "admin_promo_create_enter_discount_prompt")
        )
    else:
        await state.update_data(discount_percent=0)
        await state.set_state(AdminPromoStates.awaiting_activations)
        await callback.message.edit_text(
            t(user.language, "admin_promo_create_enter_activations_prompt")
        )
    await callback.answer()


@router.message(StateFilter(AdminPromoStates.awaiting_discount), F.text)
async def handle_promo_create_discount(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        discount = int(message.text.strip().rstrip("%"))
        if not (0 < discount <= 100):
            raise ValueError
    except ValueError:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(discount_percent=discount)
    await state.set_state(AdminPromoStates.awaiting_activations)
    await message.answer(t(user.language, "admin_promo_create_enter_activations_prompt"))


@router.message(StateFilter(AdminPromoStates.awaiting_activations), F.text)
async def handle_promo_create_activations(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        activations = int(message.text.strip())
        if activations <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    if plan is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    kind = PromoKind(data["kind"])
    await message.answer(
        t(
            user.language,
            "admin_promo_create_confirm",
            plan_title=plan.title(user.language),
            kind=t(
                user.language,
                "promo_kind_full" if kind == PromoKind.FULL_PREMIUM else "promo_kind_discount",
            ),
            discount_percent=data.get("discount_percent", 0),
            activations=activations,
        )
    )
    promo = await PromoService(uow).create_admin_code(
        plan=plan,
        kind=kind,
        discount_percent=data.get("discount_percent", 0),
        activations=activations,
    )
    await record_admin_action(
        uow,
        user,
        action="create_admin_promo",
        entity_type="promo_code",
        entity_id=str(promo.id),
        after={"code": promo.code, "plan_id": plan.id, "activations": activations},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_promo_create_success", code=promo.code),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:promos")]
        ),
    )
