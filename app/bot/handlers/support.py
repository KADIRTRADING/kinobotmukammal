"""Help/support: /terms, /privacy, /support commands and the Help menu
button that opens or continues a ticket thread. Notifies admins of new
support requests.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import SupportStates
from app.config import get_settings
from app.db.models.enums import AdminRole, SupportSenderType
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t

router = Router(name="support")
settings = get_settings()

_TERMS_URL_PATH = "/legal/terms"
_PRIVACY_URL_PATH = "/legal/privacy"


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(Command("terms"))
async def handle_terms(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(
            user.language,
            "support_terms_command",
            url=f"{settings.PUBLIC_BASE_URL}{_TERMS_URL_PATH}",
        )
    )


@router.message(Command("privacy"))
async def handle_privacy(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(
        t(
            user.language,
            "support_privacy_command",
            url=f"{settings.PUBLIC_BASE_URL}{_PRIVACY_URL_PATH}",
        )
    )


@router.message(Command("support"))
@router.message(F.text.in_(_menu_texts("menu_help")))
async def handle_support_menu(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(SupportStates.awaiting_message)
    await message.answer(t(user.language, "support_menu_title"))


@router.message(StateFilter(SupportStates.awaiting_message), F.text)
async def handle_support_message(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    ticket = await uow.support.get_open_ticket_for_user(user.id)
    if ticket is None:
        ticket = await uow.support.create_ticket(user_id=user.id, subject=message.text[:64])

    await uow.support.add_message(
        ticket_id=ticket.id,
        sender_type=SupportSenderType.USER,
        sender_id=user.id,
        text=message.text,
    )
    await message.answer(t(user.language, "support_ticket_created", ticket_id=ticket.id))
    await state.clear()

    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.SUPPORT]
    )
    text = t(
        "en",
        "admin_notify_support_request",
        user=f"@{user.username}" if user.username else str(user.telegram_id),
        ticket_id=ticket.id,
    )
    for admin in admins:
        try:
            await message.bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue
