"""Promo code menu: create (user/blogger), list mine, and redeem.

Follows spec section 7's exact prompts: kind -> plan -> discount (if
applicable) -> activation count -> issuer label (User/Blogger) ->
attribution link (yes/no -> value) -> confirmation showing plan, discount,
activation count, total cost, current balance, and balance after
reservation.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.promo import (
    promo_attribution_choice_keyboard,
    promo_confirm_keyboard,
    promo_issuer_keyboard,
    promo_kind_keyboard,
    promo_menu_keyboard,
    promo_plan_keyboard,
)
from app.bot.states import PromoCreationStates, PromoRedeemStates
from app.db.models.enums import AdminRole, PromoKind
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.blogger_service import BloggerService
from app.services.promo_service import AttributionRequest, PromoService

router = Router(name="promo")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_my_promo_codes")))
async def handle_promo_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(user.language, "promo_menu_title"), reply_markup=promo_menu_keyboard(user.language)
    )


@router.callback_query(F.data == "promo:mine")
async def handle_promo_mine(callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs) -> None:
    codes = await uow.promos.list_by_issuer(user.id)
    if not codes:
        await callback.message.answer(t(user.language, "promo_my_codes_empty"))
    else:
        lines = [
            t(
                user.language,
                "promo_code_status_line",
                code=c.code,
                remaining=c.remaining_uses,
                max_uses=c.max_uses,
                status=c.moderation_status,
            )
            for c in codes
        ]
        await callback.message.answer("\n".join(lines))
    await callback.answer()


# --- Creation flow -------------------------------------------------------------


@router.callback_query(F.data == "promo:create")
async def handle_promo_create_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(PromoCreationStates.choosing_kind)
    await callback.message.answer(
        t(user.language, "promo_choose_kind"), reply_markup=promo_kind_keyboard(user.language)
    )
    await callback.answer()


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_kind), F.data.startswith("promo_kind:")
)
async def handle_promo_kind_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    kind = callback.data.split(":", 1)[1]
    await state.update_data(kind=kind)
    plans = await uow.plans.list_active()
    await state.set_state(PromoCreationStates.choosing_plan)
    await callback.message.answer(
        t(user.language, "promo_choose_plan"),
        reply_markup=promo_plan_keyboard(plans, user.language),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_plan), F.data.startswith("promo_plan:")
)
async def handle_promo_plan_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":", 1)[1])
    await state.update_data(plan_id=plan_id)
    data = await state.get_data()
    if data["kind"] == PromoKind.PERCENT_DISCOUNT.value:
        await state.set_state(PromoCreationStates.entering_discount)
        await callback.message.answer(t(user.language, "promo_enter_discount_percent"))
    else:
        await state.update_data(discount_percent=0)
        await _ask_activation_count(callback.message, uow, user, state)
    await callback.answer()


@router.message(StateFilter(PromoCreationStates.entering_discount), F.text)
async def handle_discount_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        discount = int(message.text.strip().rstrip("%"))
    except ValueError:
        await message.answer(t(user.language, "error_generic"))
        return
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    if not (0 < discount <= plan.max_discount_percent):
        await message.answer(t(user.language, "error_generic"))
        return
    await state.update_data(discount_percent=discount)
    await _ask_activation_count(message, uow, user, state)


async def _ask_activation_count(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    kind = PromoKind(data["kind"])
    promo_service = PromoService(uow)
    quote = await promo_service.quote_funding(
        plan=plan,
        kind=kind,
        discount_percent=data.get("discount_percent", 0),
        requested_activations=1,
        issuer_user_id=user.id,
    )
    await state.set_state(PromoCreationStates.entering_activations)
    await message.answer(
        t(
            user.language,
            "promo_enter_activation_count",
            max_activations=quote.max_activations_affordable,
        )
    )


@router.message(StateFilter(PromoCreationStates.entering_activations), F.text)
async def handle_activations_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        activations = int(message.text.strip())
    except ValueError:
        await message.answer(t(user.language, "error_generic"))
        return
    if activations <= 0:
        await message.answer(t(user.language, "error_generic"))
        return

    await state.update_data(activations=activations)
    is_blogger = await BloggerService(uow).is_active_blogger(user.id)
    await state.set_state(PromoCreationStates.choosing_issuer)
    await message.answer(
        t(user.language, "promo_issuer_choice_prompt"),
        reply_markup=promo_issuer_keyboard(user.language, is_blogger=is_blogger),
    )


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_issuer), F.data.startswith("promo_issuer:")
)
async def handle_issuer_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    issuer_kind = callback.data.split(":", 1)[1]
    await state.update_data(issuer_is_blogger=(issuer_kind == "blogger"))
    await state.set_state(PromoCreationStates.choosing_attribution)
    await callback.message.answer(
        t(user.language, "promo_attribution_prompt"),
        reply_markup=promo_attribution_choice_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_attribution), F.data == "promo_attr:no"
)
async def handle_attribution_no(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(attribution_kind="none", attribution_value=None)
    await _show_promo_confirmation(callback.message, uow, user, state)
    await callback.answer()


@router.callback_query(
    StateFilter(PromoCreationStates.choosing_attribution), F.data == "promo_attr:yes"
)
async def handle_attribution_yes(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(PromoCreationStates.entering_attribution_value)
    await callback.message.answer(t(user.language, "promo_attribution_enter"))
    await callback.answer()


@router.message(StateFilter(PromoCreationStates.entering_attribution_value), F.text)
async def handle_attribution_value_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    value = message.text.strip()
    if value.startswith("@") or (
        value.replace("_", "").isalnum() and "." not in value and "/" not in value
    ):
        kind = "telegram_user"
    elif "t.me/" in value or value.startswith("https://t.me/"):
        kind = "telegram_channel"
    else:
        kind = "external_url"
    await state.update_data(attribution_kind=kind, attribution_value=value)
    await _show_promo_confirmation(message, uow, user, state)


async def _show_promo_confirmation(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    kind = PromoKind(data["kind"])
    promo_service = PromoService(uow)
    quote = await promo_service.quote_funding(
        plan=plan,
        kind=kind,
        discount_percent=data.get("discount_percent", 0),
        requested_activations=data["activations"],
        issuer_user_id=user.id,
    )
    await state.update_data(
        quote_total=quote.total_reserved_amount, quote_balance_before=quote.balance_before
    )

    if not quote.sufficient_funds:
        await message.answer(
            t(
                user.language,
                "promo_insufficient_funds",
                required=quote.total_reserved_amount,
                available=quote.balance_before,
                currency=plan.currency,
            )
        )
        await state.clear()
        return

    await state.set_state(PromoCreationStates.confirming)
    await message.answer(
        t(
            user.language,
            "promo_confirm_summary",
            plan_title=plan.title(user.language),
            kind=t(
                user.language,
                "promo_kind_full" if kind == PromoKind.FULL_PREMIUM else "promo_kind_discount",
            ),
            discount_percent=quote.discount_percent,
            activations=data["activations"],
            total_cost=quote.total_reserved_amount,
            currency=plan.currency,
            balance_before=quote.balance_before,
            balance_after=quote.balance_after,
        ),
        reply_markup=promo_confirm_keyboard(user.language),
    )


@router.callback_query(StateFilter(PromoCreationStates.confirming), F.data == "promo_confirm:no")
async def handle_promo_confirm_no(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await callback.message.answer(t(user.language, "action_cancelled"))
    await state.clear()
    await callback.answer()


@router.callback_query(StateFilter(PromoCreationStates.confirming), F.data == "promo_confirm:yes")
async def handle_promo_confirm_yes(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    kind = PromoKind(data["kind"])
    promo_service = PromoService(uow)

    try:
        promo = await promo_service.create_user_code(
            issuer_user_id=user.id,
            issuer_is_blogger=data.get("issuer_is_blogger", False),
            plan=plan,
            kind=kind,
            discount_percent=data.get("discount_percent", 0),
            activations=data["activations"],
            attribution=AttributionRequest(
                kind=data.get("attribution_kind", "none"), value=data.get("attribution_value")
            ),
        )
    except ValueError as exc:
        await callback.message.answer(str(exc))
        await state.clear()
        await callback.answer()
        return

    if promo.moderation_status == "pending":
        await callback.message.answer(
            t(user.language, "promo_created_pending_review", code=promo.code)
        )
        await _notify_admins_promo_review(callback, uow, promo)
    else:
        await callback.message.answer(t(user.language, "promo_created_success", code=promo.code))

    await state.clear()
    await callback.answer()


async def _notify_admins_promo_review(callback: CallbackQuery, uow: UnitOfWork, promo) -> None:
    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN]
    )
    text = t("en", "admin_notify_promo_review_needed", code=promo.code, issuer=promo.issuer_user_id)
    for admin in admins:
        try:
            await callback.bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue


# --- Redeem flow ---------------------------------------------------------------


@router.callback_query(F.data == "promo:redeem")
async def handle_promo_redeem_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(PromoRedeemStates.awaiting_code)
    await callback.message.answer(t(user.language, "promo_enter_code_to_redeem"))
    await callback.answer()


@router.message(StateFilter(PromoRedeemStates.awaiting_code), F.text)
async def handle_promo_redeem_code(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    promo_service = PromoService(uow)
    result = await promo_service.redeem(code=message.text.strip(), redeemer_user_id=user.id)
    await state.clear()

    if not result.ok:
        key_map = {
            "not_found": "promo_redeem_not_found",
            "not_redeemable": "promo_redeem_not_redeemable",
            "cannot_redeem_own_code": "promo_redeem_own_code",
            "already_redeemed_by_user": "promo_redeem_already_used",
        }
        await message.answer(t(user.language, key_map.get(result.reason, "error_generic")))
        return

    if result.is_full_premium:
        from app.db.models.enums import EntitlementSource
        from app.services.entitlement_service import EntitlementService

        entitlement_service = EntitlementService(uow)
        await entitlement_service.grant(
            user_id=user.id,
            plan_id=result.plan.id,
            duration_days=result.plan.duration_days,
            source=EntitlementSource.PROMO,
            source_reference=f"promo:{result.promo.id}:{user.id}",
        )
        await message.answer(t(user.language, "promo_redeem_success_full"))
    else:
        await message.answer(
            t(
                user.language,
                "promo_redeem_success_discount",
                amount=result.buyer_amount_due,
                currency=result.plan.currency,
            )
        )
        # Remainder payment: reuse the premium checkout with the pre-applied
        # discount so the buyer completes payment through an allowed flow.
        from app.bot.states import PremiumCheckoutStates

        await state.update_data(
            plan_id=result.plan.id,
            discount_percent=result.discount_percent,
            promo_code=result.promo.code,
        )
        await state.set_state(PremiumCheckoutStates.choosing_payment_method)
        from app.bot.handlers.premium import _show_payment_methods

        await _show_payment_methods(message, uow, user, state)
