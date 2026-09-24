"""Admin panel entry point: the "🛠 Admin panel" reply-keyboard button and
the top-level inline menu it opens, plus the universal "back"/"exit"/
"cancel"/"noop" callbacks shared by every admin sub-section.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.admin_common import admin_menu_root_keyboard
from app.bot.keyboards.common import main_menu_keyboard_for_telegram_id
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t

router = Router(name="admin_root")


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("admin_menu_button")))
async def handle_admin_menu_button(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await message.answer(
        t(user.language, "admin_panel_title"), reply_markup=admin_menu_root_keyboard(user.language)
    )


@router.callback_query(F.data == "adm:root")
async def handle_admin_root(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_panel_title"), reply_markup=admin_menu_root_keyboard(user.language)
    )
    await callback.answer()


@router.callback_query(F.data == "adm:exit")
async def handle_admin_exit(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.answer(
        t(user.language, "main_menu_title"),
        reply_markup=await main_menu_keyboard_for_telegram_id(user.language, user.telegram_id, uow),
    )
    await callback.answer()


@router.callback_query(F.data == "adm:cancel")
async def handle_admin_cancel(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_action_cancelled") + "\n\n" + t(user.language, "admin_panel_title"),
        reply_markup=admin_menu_root_keyboard(user.language),
    )
    await callback.answer()


@router.callback_query(F.data == "adm:noop")
async def handle_admin_noop(callback: CallbackQuery, **kwargs) -> None:
    """The page-indicator button (e.g. "3/7") in pagination rows -- purely
    informational, never navigates anywhere."""
    await callback.answer()
