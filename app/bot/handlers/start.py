"""`/start` handler: first-run language selection, referral attribution,
and deep-link movie opening (`?start=movie_<code>`), plus language-change
callback handling.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from app.bot.handlers.admin_panel import is_admin_user
from app.bot.keyboards.common import language_selection_keyboard, main_menu_keyboard
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.referral_service import ReferralService

router = Router(name="start")


@router.message(CommandStart())
async def handle_start(message: Message, command: CommandObject, uow: UnitOfWork, **kwargs) -> None:
    tg_user = message.from_user
    user = await uow.users.get_by_telegram_id(tg_user.id)

    deep_link_arg = (command.args or "").strip()

    if user is None:
        user = await uow.users.create(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language="uz",
        )
        referral_code = (
            deep_link_arg if deep_link_arg and not deep_link_arg.startswith("movie_") else None
        )
        await ReferralService(uow).attribute_start(new_user=user, referral_code=referral_code)
    else:
        await uow.users.touch_start(user)

    if deep_link_arg.startswith("movie_"):
        from app.bot.handlers.movies import send_movie_by_code

        code = deep_link_arg[len("movie_") :]
        await send_movie_by_code(message, uow=uow, user=user, code=code)
        return

    if not user.language_selected:
        await message.answer(
            t(user.language, "choose_language"), reply_markup=language_selection_keyboard()
        )
        return

    channels = await uow.catalog.list_active_channels()
    if channels and not user.is_premium_active:
        from app.bot.handlers.movies import _get_membership_checker, ensure_channel_invite_link
        from app.bot.keyboards.movies import join_channels_keyboard

        checker = await _get_membership_checker(message.bot, uow)
        missing = []
        for ch in channels:
            if not await checker(user.telegram_id, ch.chat_id):
                missing.append(ch)
        if missing:
            for ch in missing:
                await ensure_channel_invite_link(message.bot, ch, uow)
            await message.answer(
                t(user.language, "movie_must_join_channels"),
                reply_markup=join_channels_keyboard(missing, 0, user.language),
            )
            return

    is_admin = await is_admin_user(user.telegram_id, uow)
    await message.answer(
        t(user.language, "main_menu_title"),
        reply_markup=main_menu_keyboard(user.language, is_admin=is_admin),
    )


@router.callback_query(F.data.startswith("lang:"))
async def handle_language_choice(callback: CallbackQuery, uow: UnitOfWork, **kwargs) -> None:
    language = callback.data.split(":", 1)[1]
    if language not in SUPPORTED_LANGUAGES:
        await callback.answer()
        return

    user = await uow.users.get_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer()
        return

    await uow.users.set_language(user, language)
    await callback.message.edit_text(t(language, "language_set"))

    channels = await uow.catalog.list_active_channels()
    if channels and not user.is_premium_active:
        from app.bot.handlers.movies import _get_membership_checker, ensure_channel_invite_link
        from app.bot.keyboards.movies import join_channels_keyboard

        checker = await _get_membership_checker(callback.bot, uow)
        missing = []
        for ch in channels:
            if not await checker(user.telegram_id, ch.chat_id):
                missing.append(ch)
        if missing:
            for ch in missing:
                await ensure_channel_invite_link(callback.bot, ch, uow)
            await callback.message.answer(
                t(language, "movie_must_join_channels"),
                reply_markup=join_channels_keyboard(missing, 0, language),
            )
            await callback.answer()
            return

    is_admin = await is_admin_user(user.telegram_id, uow)
    await callback.message.answer(
        t(language, "main_menu_title"),
        reply_markup=main_menu_keyboard(language, is_admin=is_admin),
    )
    await callback.answer()
