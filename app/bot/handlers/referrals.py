"""Invite Friends menu: referral link + statistics + blogger CTA."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.bot.keyboards.referrals import referral_menu_keyboard
from app.config import get_settings
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.blogger_service import BloggerService
from app.services.referral_service import ReferralService

router = Router(name="referrals")
settings = get_settings()


def _menu_texts(key: str) -> set[str]:
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


@router.message(F.text.in_(_menu_texts("menu_invite_friends")))
async def handle_invite_friends_menu(
    message: Message, uow: UnitOfWork, user: User, **kwargs
) -> None:
    link = f"https://t.me/{settings.BOT_USERNAME}?start={user.referral_code}"
    await message.answer(t(user.language, "referral_link_title", link=link))

    stats = await ReferralService(uow).stats_for_referrer(user.id)
    await message.answer(
        t(
            user.language,
            "referral_stats_title",
            total_joins=stats["total_joins"],
            qualified_joins=stats["qualified_joins"],
            purchase_commission_total=stats["purchase_commission_total"],
            blogger_reward_total=stats["blogger_reward_total"],
        )
    )

    is_blogger = await BloggerService(uow).is_active_blogger(user.id)
    if not is_blogger and user.blogger_status_cache != "pending":
        await message.answer(
            t(user.language, "referral_become_blogger_prompt"),
            reply_markup=referral_menu_keyboard(user.language, show_blogger_cta=True),
        )
