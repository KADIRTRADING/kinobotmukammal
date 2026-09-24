"""Admin Premium Plans section: create, edit, activate/deactivate, set
duration and price, and view current plans -- each plan independently
configuring its own price, standard/blogger referral percentages, and
promo discount cap (spec section 3: never hard-coded globally).
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_common import admin_back_row
from app.bot.keyboards.admin_plans import admin_plan_detail_keyboard, admin_plans_menu_keyboard
from app.bot.states import AdminPlanStates
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t

router = Router(name="admin_plans")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:plans")
async def handle_plans_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    plans = await uow.plans.list_all()
    await callback.message.edit_text(
        t(user.language, "admin_plans_menu_title"),
        reply_markup=admin_plans_menu_keyboard(plans, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ap:view:"))
async def handle_plan_view(callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs) -> None:
    plan_id = int(callback.data.split(":")[2])
    plan = await uow.plans.get(plan_id)
    if plan is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    status = "✅" if plan.is_active else "⛔"
    await callback.message.edit_text(
        t(
            user.language,
            "admin_plan_detail_title",
            title=_esc(plan.title(user.language)),
            code=_esc(plan.code),
            price=plan.price_amount,
            currency=plan.currency,
            duration_days=plan.duration_days,
            standard_percent=plan.standard_referral_percent / 100,
            blogger_percent=plan.blogger_referral_percent / 100,
            max_discount=plan.max_discount_percent,
            status=status,
        ),
        reply_markup=admin_plan_detail_keyboard(plan, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ap:toggle:"))
async def handle_plan_toggle(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    plan_id = int(callback.data.split(":")[2])
    plan = await uow.plans.get(plan_id)
    if plan is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    new_state = not plan.is_active
    await uow.plans.update(plan, is_active=new_state)
    await record_admin_action(
        uow,
        user,
        action="toggle_plan",
        entity_type="premium_plan",
        entity_id=str(plan_id),
        after={"is_active": new_state},
    )
    key = "admin_plan_activated" if new_state else "admin_plan_deactivated"
    await callback.answer(t(user.language, key, code=plan.code), show_alert=True)
    await handle_plan_view(callback, uow, user, **kwargs)


# --- Edit price / referral percentages -------------------------------------------


@router.callback_query(F.data.startswith("ap:editprice:"))
async def handle_plan_edit_price_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":")[2])
    await state.update_data(plan_id=plan_id)
    await state.set_state(AdminPlanStates.awaiting_new_price)
    await callback.message.edit_text(t(user.language, "admin_plan_enter_price_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminPlanStates.awaiting_new_price), F.text)
async def handle_plan_new_price(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        price = int(message.text.strip())
        if price <= 0:
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
    before = {"price_amount": plan.price_amount}
    await uow.plans.update(plan, price_amount=price)
    await record_admin_action(
        uow,
        user,
        action="update_plan_price",
        entity_type="premium_plan",
        entity_id=str(plan.id),
        before=before,
        after={"price_amount": price},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_plan_updated"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"ap:view:{plan.id}")]
        ),
    )


@router.callback_query(F.data.startswith("ap:editstd:"))
async def handle_plan_edit_standard_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":")[2])
    await state.update_data(plan_id=plan_id)
    await state.set_state(AdminPlanStates.awaiting_new_standard_referral)
    await callback.message.edit_text(t(user.language, "admin_plan_enter_standard_referral_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminPlanStates.awaiting_new_standard_referral), F.text)
async def handle_plan_new_standard_referral(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    percent = _parse_percent(message.text)
    if percent is None:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    if plan is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    before = {"standard_referral_percent": plan.standard_referral_percent}
    await uow.plans.update(plan, standard_referral_percent=int(percent * 100))
    await record_admin_action(
        uow,
        user,
        action="update_plan_standard_referral",
        entity_type="premium_plan",
        entity_id=str(plan.id),
        before=before,
        after={"standard_referral_percent": int(percent * 100)},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_plan_updated"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"ap:view:{plan.id}")]
        ),
    )


@router.callback_query(F.data.startswith("ap:editblg:"))
async def handle_plan_edit_blogger_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":")[2])
    await state.update_data(plan_id=plan_id)
    await state.set_state(AdminPlanStates.awaiting_new_blogger_referral)
    await callback.message.edit_text(t(user.language, "admin_plan_enter_blogger_referral_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminPlanStates.awaiting_new_blogger_referral), F.text)
async def handle_plan_new_blogger_referral(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    percent = _parse_percent(message.text)
    if percent is None:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    if plan is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    before = {"blogger_referral_percent": plan.blogger_referral_percent}
    await uow.plans.update(plan, blogger_referral_percent=int(percent * 100))
    await record_admin_action(
        uow,
        user,
        action="update_plan_blogger_referral",
        entity_type="premium_plan",
        entity_id=str(plan.id),
        before=before,
        after={"blogger_referral_percent": int(percent * 100)},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_plan_updated"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"ap:view:{plan.id}")]
        ),
    )


def _parse_percent(text: str) -> float | None:
    try:
        value = float(text.strip().rstrip("%"))
    except ValueError:
        return None
    if not (0 <= value <= 100):
        return None
    return value


# --- Create plan ------------------------------------------------------------------


@router.callback_query(F.data == "ap:add")
async def handle_plan_add_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(AdminPlanStates.awaiting_code)
    await callback.message.edit_text(
        t(user.language, "admin_plan_enter_code_prompt"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:plans")]
        ),
    )
    await callback.answer()


@router.message(StateFilter(AdminPlanStates.awaiting_code), F.text)
async def handle_plan_code_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    code = message.text.strip()
    existing = await uow.plans.get_by_code(code)
    if existing is not None:
        await message.answer(t(user.language, "admin_plan_code_taken"))
        return
    await state.update_data(code=code)
    await state.set_state(AdminPlanStates.awaiting_title_uz)
    await message.answer(t(user.language, "admin_plan_enter_title_uz_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_title_uz), F.text)
async def handle_plan_title_uz(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title_uz=message.text.strip())
    await state.set_state(AdminPlanStates.awaiting_title_ru)
    await message.answer(t(user.language, "admin_plan_enter_title_ru_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_title_ru), F.text)
async def handle_plan_title_ru(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title_ru=message.text.strip())
    await state.set_state(AdminPlanStates.awaiting_title_en)
    await message.answer(t(user.language, "admin_plan_enter_title_en_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_title_en), F.text)
async def handle_plan_title_en(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title_en=message.text.strip())
    await state.set_state(AdminPlanStates.awaiting_duration)
    await message.answer(t(user.language, "admin_plan_enter_duration_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_duration), F.text)
async def handle_plan_duration(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(duration_days=duration)
    await state.set_state(AdminPlanStates.awaiting_price)
    await message.answer(t(user.language, "admin_plan_enter_price_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_price), F.text)
async def handle_plan_price(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        price = int(message.text.strip())
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(price_amount=price)
    await state.set_state(AdminPlanStates.awaiting_currency)
    await message.answer(t(user.language, "admin_plan_enter_currency_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_currency), F.text)
async def handle_plan_currency(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    currency = message.text.strip().upper()
    if not (2 <= len(currency) <= 8):
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(currency=currency)
    await state.set_state(AdminPlanStates.awaiting_standard_referral)
    await message.answer(t(user.language, "admin_plan_enter_standard_referral_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_standard_referral), F.text)
async def handle_plan_standard_referral(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    percent = _parse_percent(message.text)
    if percent is None:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(standard_referral_percent=int(percent * 100))
    await state.set_state(AdminPlanStates.awaiting_blogger_referral)
    await message.answer(t(user.language, "admin_plan_enter_blogger_referral_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_blogger_referral), F.text)
async def handle_plan_blogger_referral(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    percent = _parse_percent(message.text)
    if percent is None:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(blogger_referral_percent=int(percent * 100))
    await state.set_state(AdminPlanStates.awaiting_max_discount)
    await message.answer(t(user.language, "admin_plan_enter_max_discount_prompt"))


@router.message(StateFilter(AdminPlanStates.awaiting_max_discount), F.text)
async def handle_plan_max_discount(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    percent = _parse_percent(message.text)
    if percent is None:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    data = await state.get_data()
    plan = await uow.plans.create(
        code=data["code"],
        title_uz=data["title_uz"],
        title_ru=data["title_ru"],
        title_en=data["title_en"],
        duration_days=data["duration_days"],
        price_amount=data["price_amount"],
        currency=data["currency"],
        standard_referral_percent=data["standard_referral_percent"],
        blogger_referral_percent=data["blogger_referral_percent"],
        max_discount_percent=int(percent),
        is_active=True,
    )
    await record_admin_action(
        uow,
        user,
        action="create_plan",
        entity_type="premium_plan",
        entity_id=str(plan.id),
        after={"code": plan.code, "price_amount": plan.price_amount},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_plan_created", code=_esc(plan.code)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:plans")]
        ),
    )
