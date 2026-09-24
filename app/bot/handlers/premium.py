"""Premium plan selection, promo entry, payment-method choice, checkout
confirmation, and Telegram Stars invoice + successful_payment handling.

Wallet checkout (paying for premium out of the user's OWN balance) is
implemented here because it never leaves Telegram and never asks a bot
user to visit an external checkout page -- it is a same-currency ledger
debit, not a digital-goods payment routed around Telegram's own in-app
purchase flow (see README "Payments and platform compliance").
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from app.bot.keyboards.common import confirm_keyboard, main_menu_keyboard_for_telegram_id
from app.bot.keyboards.premium import (
    payment_method_keyboard,
    plan_list_keyboard,
    skip_promo_keyboard,
)
from app.bot.states import PremiumCheckoutStates
from app.config import get_settings
from app.db.models.enums import PaymentProviderCode
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.payments.registry import PaymentRegistry
from app.services.promo_service import PromoService
from app.services.purchase_service import PurchaseService
from app.services.wallet_service import WalletService

router = Router(name="premium")
settings = get_settings()


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_premium")))
async def handle_premium_menu(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    if user.is_premium_active:
        await message.answer(
            t(user.language, "premium_already_active", until=user.premium_until.isoformat())
        )
        return
    plans = await uow.plans.list_active()
    if not plans:
        await message.answer(t(user.language, "error_generic"))
        return
    await state.set_state(PremiumCheckoutStates.choosing_plan)
    await message.answer(
        t(user.language, "premium_plans_title"),
        reply_markup=plan_list_keyboard(plans, user.language),
    )


@router.callback_query(StateFilter(PremiumCheckoutStates.choosing_plan), F.data.startswith("plan:"))
async def handle_plan_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":", 1)[1])
    plan = await uow.plans.get(plan_id)
    if plan is None or not plan.is_active:
        await callback.answer(t(user.language, "error_generic"), show_alert=True)
        return
    await state.update_data(plan_id=plan_id, discount_percent=0, promo_code=None)
    await state.set_state(PremiumCheckoutStates.entering_promo)
    await callback.message.answer(
        t(user.language, "premium_enter_promo_code"),
        reply_markup=skip_promo_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(StateFilter(PremiumCheckoutStates.entering_promo), F.data == "promo:skip")
async def handle_promo_skip(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await _show_payment_methods(callback.message, uow, user, state)
    await callback.answer()


@router.message(StateFilter(PremiumCheckoutStates.entering_promo), F.text)
async def handle_promo_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])

    promo = await uow.promos.get_by_code(message.text.strip())
    if promo is None or not promo.is_redeemable or promo.plan_id != plan.id:
        await message.answer(t(user.language, "premium_promo_invalid"))
        return

    discount_percent = 0 if promo.kind == "full_premium" else promo.discount_percent
    await state.update_data(
        discount_percent=discount_percent,
        promo_code=promo.code,
        is_full_premium=(promo.kind == "full_premium"),
    )

    purchase_service = PurchaseService(uow)
    quote = await purchase_service.quote(plan, discount_percent=discount_percent)
    await message.answer(
        t(user.language, "premium_promo_applied", amount=quote.net_amount, currency=quote.currency)
    )
    await _show_payment_methods(message, uow, user, state)


async def _show_payment_methods(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    plan_id = data["plan_id"]
    if data.get("is_full_premium"):
        # Full-premium promo: no payment needed at all, redeem immediately.
        await _finalize_full_premium_promo(message, uow, user, state)
        return

    registry = PaymentRegistry(settings, bot=message.bot)
    stars_enabled = registry.is_provider_enabled("telegram_stars")
    plan = await uow.plans.get(plan_id)
    wallet_enabled = (
        True  # wallet checkout is always offered; insufficient funds is handled at confirm time
    )

    await state.set_state(PremiumCheckoutStates.choosing_payment_method)
    await message.answer(
        t(
            user.language,
            "premium_plan_details",
            title=plan.title(user.language),
            duration_days=plan.duration_days,
            price=plan.price_amount,
            currency=plan.currency,
        ),
        reply_markup=payment_method_keyboard(
            user.language, plan_id, stars_enabled=stars_enabled, wallet_enabled=wallet_enabled
        ),
    )


async def _finalize_full_premium_promo(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext
) -> None:
    data = await state.get_data()
    promo_service = PromoService(uow)
    result = await promo_service.redeem(code=data["promo_code"], redeemer_user_id=user.id)
    if not result.ok:
        await message.answer(t(user.language, "promo_redeem_not_redeemable"))
        await state.clear()
        return

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
    await message.answer(
        t(user.language, "main_menu_title"),
        reply_markup=main_menu_keyboard_for_telegram_id(user.language, user.telegram_id),
    )
    await state.clear()


@router.callback_query(
    StateFilter(PremiumCheckoutStates.choosing_payment_method), F.data.startswith("pay:stars:")
)
async def handle_pay_with_stars(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    registry = PaymentRegistry(settings, bot=callback.bot)
    try:
        provider = registry.get_enabled("telegram_stars")
    except Exception:
        await callback.answer(t(user.language, "premium_provider_disabled"), show_alert=True)
        return

    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    purchase_service = PurchaseService(uow)
    quote = await purchase_service.quote(plan, discount_percent=data.get("discount_percent", 0))

    order = await purchase_service.create_order(
        buyer_user_id=user.id,
        plan=plan,
        provider_code=PaymentProviderCode.TELEGRAM_STARS,
        discount_percent=data.get("discount_percent", 0),
    )
    # Stars amounts are denominated in XTR regardless of the plan's display
    # currency; a real deployment should configure plan prices for Stars
    # checkout in XTR directly, or maintain a documented XTR price per plan.
    # Here we charge `quote.net_amount` as the XTR amount 1:1, which is
    # correct when PremiumPlan.currency == "XTR" and must be configured as
    # such by the admin for Stars-payable plans.
    charge = await provider.create_charge(
        order_uid=str(order.uid),
        amount=quote.net_amount,
        currency="XTR",
        description=plan.title(user.language),
        buyer_telegram_id=user.telegram_id,
    )
    payload = charge.checkout_payload
    await callback.message.answer_invoice(
        title=payload["title"],
        description=payload["description"],
        payload=payload["payload"],
        provider_token=payload["provider_token"],
        currency=payload["currency"],
        prices=[{"label": p["label"], "amount": p["amount"]} for p in payload["prices"]],
    )
    await state.clear()
    await callback.answer()


@router.callback_query(
    StateFilter(PremiumCheckoutStates.choosing_payment_method), F.data.startswith("pay:wallet:")
)
async def handle_pay_with_wallet(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    purchase_service = PurchaseService(uow)
    quote = await purchase_service.quote(plan, discount_percent=data.get("discount_percent", 0))

    await state.update_data(quoted_amount=quote.net_amount, quoted_currency=quote.currency)
    await state.set_state(PremiumCheckoutStates.confirming)
    await callback.message.answer(
        t(
            user.language,
            "premium_checkout_summary",
            plan_title=plan.title(user.language),
            amount=quote.net_amount,
            currency=quote.currency,
        ),
        reply_markup=confirm_keyboard(user.language, confirm_cb="wallet_checkout:confirm"),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(PremiumCheckoutStates.confirming), F.data == "wallet_checkout:confirm"
)
async def handle_wallet_checkout_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    plan = await uow.plans.get(data["plan_id"])
    amount = data["quoted_amount"]
    currency = data["quoted_currency"]

    wallet_service = WalletService(uow)
    balances = await wallet_service.get_balances(user.id)
    available = balances.get(currency, {}).get("available", 0)
    if available < amount:
        await callback.message.answer(
            t(
                user.language,
                "premium_insufficient_balance",
                available=available,
                required=amount,
                currency=currency,
            )
        )
        await state.clear()
        await callback.answer()
        return

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=user.id,
        plan=plan,
        provider_code=PaymentProviderCode.WALLET,
        discount_percent=data.get("discount_percent", 0),
    )
    from app.db.models.enums import WalletEntryType

    await wallet_service.debit_available(
        user_id=user.id,
        currency=currency,
        amount=amount,
        entry_type=WalletEntryType.WALLET_PREMIUM_PURCHASE,
        idempotency_key=f"wallet_purchase:{order.uid}",
        reference_type="order",
        reference_id=str(order.id),
    )
    await purchase_service.confirm_payment(order, provider_reference=f"wallet:{order.uid}")

    updated_user = await uow.users.get_by_id(user.id)
    await callback.message.answer(
        t(user.language, "premium_payment_success", until=updated_user.premium_until.isoformat())
    )
    await callback.message.answer(
        t(user.language, "main_menu_title"),
        reply_markup=main_menu_keyboard_for_telegram_id(user.language, user.telegram_id),
    )
    await state.clear()
    await callback.answer()


# --- Telegram Stars: pre_checkout_query + successful_payment ------------------


@router.pre_checkout_query()
async def handle_pre_checkout(
    pre_checkout_query: PreCheckoutQuery, uow: UnitOfWork, **kwargs
) -> None:
    order = await uow.orders.get_by_uid(pre_checkout_query.invoice_payload)
    if order is None or order.status != "pending":
        await pre_checkout_query.answer(
            ok=False, error_message="Order not found or already processed"
        )
        return
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def handle_successful_payment(
    message: Message, uow: UnitOfWork, user: User, **kwargs
) -> None:
    sp = message.successful_payment
    order = await uow.orders.get_by_uid(sp.invoice_payload)
    if order is None:
        return

    existing_event = await uow.orders.get_provider_event(
        "telegram_stars", sp.telegram_payment_charge_id
    )
    if existing_event is not None:
        return  # duplicate delivery of the same successful_payment update -- ignore

    await uow.orders.create_provider_event(
        provider_code="telegram_stars",
        provider_event_id=sp.telegram_payment_charge_id,
        event_type="successful_payment",
        order_id=order.id,
        raw_payload={
            "currency": sp.currency,
            "total_amount": sp.total_amount,
            "telegram_payment_charge_id": sp.telegram_payment_charge_id,
        },
        processed=True,
    )

    purchase_service = PurchaseService(uow)
    await purchase_service.confirm_payment(order, provider_reference=sp.telegram_payment_charge_id)

    updated_user = await uow.users.get_by_id(user.id)
    await message.answer(
        t(user.language, "premium_payment_success", until=updated_user.premium_until.isoformat())
    )
    await message.answer(
        t(user.language, "main_menu_title"),
        reply_markup=main_menu_keyboard_for_telegram_id(user.language, user.telegram_id),
    )
