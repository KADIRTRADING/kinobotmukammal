"""Settings menu: language change at any time (spec section 2)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.common import language_selection_keyboard
from app.bot.keyboards.settings import settings_menu_keyboard
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t

router = Router(name="settings")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_settings")))
async def handle_settings_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(user.language, "settings_menu_title"), reply_markup=settings_menu_keyboard(user.language)
    )


@router.callback_query(F.data == "settings:language")
async def handle_settings_change_language(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    await callback.message.answer(
        t(user.language, "choose_language"), reply_markup=language_selection_keyboard()
    )
    await callback.answer()
