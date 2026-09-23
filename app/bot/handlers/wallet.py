"""Balance screen: available/reserved/pending per currency, and history."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.wallet import balance_actions_keyboard
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.wallet_service import WalletService

router = Router(name="wallet")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_balance")))
async def handle_balance_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    wallet_service = WalletService(uow)
    balances = await wallet_service.get_balances(user.id)
    if not balances:
        await message.answer(t(user.language, "balance_no_wallets"))
        return
    for currency, amounts in balances.items():
        await message.answer(
            t(
                user.language,
                "balance_title",
                available=amounts["available"],
                reserved=amounts["reserved"],
                pending=amounts["pending"],
                currency=currency,
            ),
            reply_markup=balance_actions_keyboard(user.language),
        )


@router.callback_query(F.data == "wallet:history")
async def handle_wallet_history(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    wallet_service = WalletService(uow)
    entries = await wallet_service.transaction_history(user.id, limit=20)
    if not entries:
        await callback.message.answer(t(user.language, "balance_history_empty"))
        await callback.answer()
        return
    lines = [
        t(
            user.language,
            "balance_history_entry",
            date=entry.created_at.strftime("%Y-%m-%d %H:%M"),
            type=entry.entry_type,
            amount=entry.amount,
            currency=entry.currency,
        )
        for entry in entries
    ]
    await callback.message.answer(
        t(user.language, "balance_history_title") + "\n" + "\n".join(lines)
    )
    await callback.answer()
