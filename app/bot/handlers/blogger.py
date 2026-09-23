"""Blogger application flow: choose platform -> receive verification phrase
-> submit profile URL -> admin review (manual, honestly labeled).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.states import BloggerApplicationStates
from app.config import get_settings
from app.db.models.enums import AdminRole
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.blogger_service import BloggerService

router = Router(name="blogger")
settings = get_settings()


@router.callback_query(F.data == "blogger:apply")
async def handle_blogger_apply_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await callback.message.answer(t(user.language, "blogger_apply_start"))
    await callback.message.answer(t(user.language, "blogger_manual_review_notice"))
    await state.set_state(BloggerApplicationStates.choosing_platform)
    await callback.message.answer(t(user.language, "blogger_apply_choose_platform"))
    await callback.answer()


@router.message(StateFilter(BloggerApplicationStates.choosing_platform), F.text)
async def handle_platform_chosen(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    blogger_service = BloggerService(uow)
    result = await blogger_service.start_application(
        applicant_user_id=user.id, platform_name=message.text.strip()
    )
    if result.already_pending:
        await message.answer(t(user.language, "blogger_apply_already_pending"))
        await state.clear()
        return

    await state.update_data(application_id=result.application.id)
    await state.set_state(BloggerApplicationStates.awaiting_url)
    await message.answer(
        t(user.language, "blogger_apply_phrase", phrase=result.application.verification_phrase)
    )
    await message.answer(t(user.language, "blogger_apply_send_url"))


@router.message(StateFilter(BloggerApplicationStates.awaiting_url), F.text)
async def handle_url_submitted(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    application = await uow.bloggers.get_application(data["application_id"])
    if application is None:
        await message.answer(t(user.language, "error_generic"))
        await state.clear()
        return

    blogger_service = BloggerService(uow)
    await blogger_service.submit_url(application, message.text.strip())
    await blogger_service.attempt_automated_check(application)

    await message.answer(t(user.language, "blogger_apply_submitted"))
    await state.clear()

    await _notify_admins_new_application(message, uow, user, application)


async def _notify_admins_new_application(
    message: Message, uow: UnitOfWork, user: User, application
) -> None:
    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN]
    )
    text = t(
        "en",
        "admin_notify_new_blogger_application",
        user=f"@{user.username}" if user.username else str(user.telegram_id),
        platform=application.platform_name or "unknown",
    )
    for admin in admins:
        try:
            await message.bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue
