"""Gifts menu: send premium/balance to another user, view received gifts."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.gifts import gift_confirm_keyboard, gifts_menu_keyboard
from app.bot.keyboards.premium import plan_list_keyboard
from app.bot.states import GiftStates
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.gift_service import GiftService
from app.services.wallet_service import WalletService

router = Router(name="gifts")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_gifts")))
async def handle_gifts_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(user.language, "gifts_menu_title"), reply_markup=gifts_menu_keyboard(user.language)
    )


@router.callback_query(F.data == "gift:received")
async def handle_gifts_received(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    gifts = await uow.gifts.list_received(user.id)
    if not gifts:
        await callback.message.answer(t(user.language, "gift_recipient_not_found"))
    else:
        for gift in gifts[:10]:
            desc = f"{gift.kind} - {gift.created_at.strftime('%Y-%m-%d')}"
            await callback.message.answer(
                t(user.language, "gift_received_notice", description=desc)
            )
    await callback.answer()


@router.callback_query(F.data == "gift:send_premium")
async def handle_gift_premium_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(GiftStates.awaiting_recipient_premium)
    await callback.message.answer(t(user.language, "gift_enter_recipient"))
    await callback.answer()


@router.message(StateFilter(GiftStates.awaiting_recipient_premium), F.text)
async def handle_gift_premium_recipient(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    recipient = await _resolve_recipient(uow, message.text.strip())
    if recipient is None:
        await message.answer(t(user.language, "gift_recipient_not_found"))
        return
    await state.update_data(recipient_id=recipient.id, recipient_label=_recipient_label(recipient))
    plans = await uow.plans.list_active()
    await state.set_state(GiftStates.choosing_plan_premium)
    await message.answer(
        t(user.language, "premium_plans_title"),
        reply_markup=plan_list_keyboard(plans, user.language),
    )


@router.callback_query(StateFilter(GiftStates.choosing_plan_premium), F.data.startswith("plan:"))
async def handle_gift_premium_plan(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    plan_id = int(callback.data.split(":", 1)[1])
    plan = await uow.plans.get(plan_id)
    data = await state.get_data()
    await state.update_data(plan_id=plan_id)
    await state.set_state(GiftStates.confirming_premium)
    await callback.message.answer(
        t(
            user.language,
            "gift_confirm_premium",
            recipient=data["recipient_label"],
            plan_title=plan.title(user.language),
            price=plan.price_amount,
            currency=plan.currency,
        ),
        reply_markup=gift_confirm_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(StateFilter(GiftStates.confirming_premium), F.data == "gift_confirm:yes")
async def handle_gift_premium_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    gift_service = GiftService(uow)
    try:
        await gift_service.gift_premium_from_user(
            sender_user_id=user.id, recipient_user_id=data["recipient_id"], plan_id=data["plan_id"]
        )
    except Exception as exc:
        from app.services.money import InsufficientFundsError

        if isinstance(exc, InsufficientFundsError):
            await callback.message.answer(
                t(
                    user.language,
                    "premium_insufficient_balance",
                    available=exc.available,
                    required=exc.requested,
                    currency=exc.currency,
                )
            )
        else:
            await callback.message.answer(t(user.language, "error_generic"))
        await state.clear()
        await callback.answer()
        return

    await callback.message.answer(t(user.language, "gift_sent_success"))
    await state.clear()
    await callback.answer()


@router.callback_query(StateFilter(GiftStates.confirming_premium), F.data == "gift_confirm:no")
@router.callback_query(StateFilter(GiftStates.confirming_balance), F.data == "gift_confirm:no")
async def handle_gift_cancel(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await callback.message.answer(t(user.language, "action_cancelled"))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "gift:send_balance")
async def handle_gift_balance_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(GiftStates.awaiting_recipient_balance)
    await callback.message.answer(t(user.language, "gift_enter_recipient"))
    await callback.answer()


@router.message(StateFilter(GiftStates.awaiting_recipient_balance), F.text)
async def handle_gift_balance_recipient(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    recipient = await _resolve_recipient(uow, message.text.strip())
    if recipient is None:
        await message.answer(t(user.language, "gift_recipient_not_found"))
        return
    await state.update_data(recipient_id=recipient.id, recipient_label=_recipient_label(recipient))
    await state.set_state(GiftStates.entering_amount_balance)
    await message.answer(t(user.language, "gift_enter_amount"))


@router.message(StateFilter(GiftStates.entering_amount_balance), F.text)
async def handle_gift_balance_amount(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        amount = int(message.text.strip())
    except ValueError:
        await message.answer(t(user.language, "error_generic"))
        return
    if amount <= 0:
        await message.answer(t(user.language, "error_generic"))
        return

    wallet_service = WalletService(uow)
    balances = await wallet_service.get_balances(user.id)
    currency = next(iter(balances.keys()), "UZS")

    data = await state.get_data()
    await state.update_data(amount=amount, currency=currency)
    await state.set_state(GiftStates.confirming_balance)
    await message.answer(
        t(
            user.language,
            "gift_confirm_balance",
            recipient=data["recipient_label"],
            amount=amount,
            currency=currency,
        ),
        reply_markup=gift_confirm_keyboard(user.language),
    )


@router.callback_query(StateFilter(GiftStates.confirming_balance), F.data == "gift_confirm:yes")
async def handle_gift_balance_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    gift_service = GiftService(uow)
    try:
        await gift_service.gift_balance_from_user(
            sender_user_id=user.id,
            recipient_user_id=data["recipient_id"],
            currency=data["currency"],
            amount=data["amount"],
        )
    except Exception as exc:
        from app.services.money import InsufficientFundsError

        if isinstance(exc, InsufficientFundsError):
            await callback.message.answer(
                t(
                    user.language,
                    "premium_insufficient_balance",
                    available=exc.available,
                    required=exc.requested,
                    currency=exc.currency,
                )
            )
        else:
            await callback.message.answer(t(user.language, "error_generic"))
        await state.clear()
        await callback.answer()
        return

    await callback.message.answer(t(user.language, "gift_sent_success"))
    await state.clear()
    await callback.answer()


async def _resolve_recipient(uow: UnitOfWork, identifier: str):
    identifier = identifier.strip()
    if identifier.startswith("@"):
        return await uow.users.get_by_username(identifier)
    if identifier.isdigit():
        return await uow.users.get_by_telegram_id(int(identifier))
    return await uow.users.get_by_username(identifier)


def _recipient_label(recipient) -> str:
    return f"@{recipient.username}" if recipient.username else str(recipient.telegram_id)
