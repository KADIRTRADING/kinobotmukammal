"""Movie search, category browsing, mandatory-channel gating, and delivery.

`send_movie_by_code` is the single function that ever calls
`MovieAccessService.deliver_and_record_view` (which returns the raw
`video_file_id`); it is invoked from here AND from `start.py`'s deep-link
handler AND from the inline-search "Open in Bot" flow, so there is exactly
one code path that can hand a protected video to a user.
"""

from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    ChatJoinRequest,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot.keyboards.movies import (
    category_list_keyboard,
    join_channels_keyboard,
    movie_search_results_keyboard,
)
from app.config import get_settings
from app.core.redis import get_redis
from app.db.models.catalog import MandatoryChannel, Movie
from app.db.models.enums import MovieAccessType
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES, t
from app.services.movie_access_service import MovieAccessService

router = Router(name="movies")


def _menu_texts(key: str) -> set[str]:
    """All localized variants of a menu button's label, used as an aiogram
    `F.text.in_(...)` filter so the same handler matches regardless of the
    user's chosen language."""
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


async def _get_membership_checker(bot, uow: UnitOfWork | None = None):
    async def checker(telegram_id: int, chat_id: str) -> bool:
        chat_id_str = str(chat_id).strip()

        # 1. Join request check:
        # "if person sent request to join accept it is like followed"
        try:
            redis = get_redis()
            if await redis.get(f"cjr:{chat_id_str}:{telegram_id}"):
                return True
        except Exception:
            pass

        if uow is not None:
            try:
                if await uow.catalog.has_join_request(chat_id_str, telegram_id):
                    return True
            except Exception:
                pass

        # 2. Live Telegram get_chat_member
        try:
            cid = (
                int(chat_id_str)
                if (chat_id_str.startswith("-") or chat_id_str.isdigit())
                else chat_id_str
            )
            member = await bot.get_chat_member(chat_id=cid, user_id=telegram_id)
            if member.status in ("member", "administrator", "creator"):
                return True
            if member.status == "restricted" and getattr(member, "is_member", True):
                return True
        except Exception:
            pass

        return False

    return checker


async def ensure_channel_invite_link(
    bot, channel: MandatoryChannel, uow: UnitOfWork | None = None
) -> str:
    """Ensures that the channel has a valid, clickable Telegram invite URL.
    Works for private channels, groups, and join-request channels."""
    if channel.invite_link and not channel.invite_link.startswith("https://t.me/-"):
        return channel.invite_link

    chat_id_str = channel.chat_id.strip()
    if chat_id_str.startswith("@") or (
        not chat_id_str.startswith("-") and not chat_id_str.isdigit()
    ):
        link = f"https://t.me/{chat_id_str.lstrip('@')}"
        channel.invite_link = link
        if uow is not None:
            await uow.session.flush()
        return link

    try:
        cid = int(chat_id_str)
        link_obj = await bot.create_chat_invite_link(chat_id=cid)
        channel.invite_link = link_obj.invite_link
        if uow is not None:
            await uow.session.flush()
        return link_obj.invite_link
    except Exception:
        try:
            cid = int(chat_id_str)
            inv = await bot.export_chat_invite_link(chat_id=cid)
            channel.invite_link = inv
            if uow is not None:
                await uow.session.flush()
            return inv
        except Exception:
            pass

    return channel.invite_link or ""


@router.message(F.text.in_(_menu_texts("menu_search_movie")))
async def handle_search_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    await message.answer(t(user.language, "movie_enter_code_or_name"))


@router.message(F.text.in_(_menu_texts("menu_categories")))
async def handle_categories_menu(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    categories = await uow.catalog.list_active_categories()
    await message.answer(
        t(user.language, "movie_categories_title"),
        reply_markup=category_list_keyboard(categories, user.language),
    )


@router.callback_query(F.data.startswith("cat:"))
async def handle_category_selected(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    category_id = int(callback.data.split(":", 1)[1])
    movies = await uow.catalog.list_by_category(category_id)
    if not movies:
        await callback.message.answer(t(user.language, "movie_no_movies_in_category"))
    else:
        await callback.message.answer(
            t(user.language, "movie_search_results"),
            reply_markup=movie_search_results_keyboard(movies, user.language),
        )
    await callback.answer()


async def handle_movie_query_text(
    message: Message, uow: UnitOfWork, user: User | None = None, **kwargs
) -> None:
    """Called by `app.bot.handlers.fallback_text`'s catch-all router, which
    is registered LAST in `register_all` so every other feature router
    (premium/wallet/promo/gifts/support/settings menu buttons, FSM text
    steps) gets first refusal on a text message. Anything that reaches here
    is treated as a movie code/name search query."""
    text = (message.text or "").strip()
    if "@" in text:
        text = re.sub(r"@\w+", "", text).strip()
    lang = user.language if user else DEFAULT_LANGUAGE

    if not text:
        await message.answer(t(lang, "movie_enter_code_or_name"))
        return

    access_service = MovieAccessService(uow)
    results = await access_service.find_by_code_or_search(text)
    if not results:
        await message.answer(t(lang, "movie_not_found"))
        return
    if len(results) == 1:
        await _present_movie(message, uow, user, results[0], bot=message.bot)
        return
    await message.answer(
        t(lang, "movie_search_results"),
        reply_markup=movie_search_results_keyboard(results, lang),
    )


@router.callback_query(F.data.startswith("movie:"))
async def handle_movie_selected(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    movie_id = int(callback.data.split(":", 1)[1])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "movie_not_found"), show_alert=True)
        return
    await _present_movie(callback.message, uow, user, movie, bot=callback.bot)
    await callback.answer()


@router.callback_query(F.data.startswith("check_membership:"))
async def handle_check_membership(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    raw_id = callback.data.split(":", 1)[1]
    if raw_id in ("0", "start"):
        checker = await _get_membership_checker(callback.bot, uow)
        channels = await uow.catalog.list_active_channels()
        missing = []
        for ch in channels:
            if not await checker(user.telegram_id, ch.chat_id):
                missing.append(ch)
        if missing:
            for ch in missing:
                await ensure_channel_invite_link(callback.bot, ch, uow)
            await callback.answer(t(user.language, "movie_still_not_joined"), show_alert=True)
            return
        try:
            await callback.message.delete()
        except Exception:
            pass
        from app.bot.keyboards.common import main_menu_keyboard

        await callback.message.answer(
            t(user.language, "main_menu_title"), reply_markup=main_menu_keyboard(user.language)
        )
        await callback.answer()
        return

    movie_id = int(raw_id)
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "movie_not_found"), show_alert=True)
        return
    await _present_movie(callback.message, uow, user, movie, bot=callback.bot, is_recheck=True)
    await callback.answer()


@router.callback_query(F.data.startswith("group_watch:"))
async def handle_group_watch(callback: CallbackQuery, uow: UnitOfWork, **kwargs) -> None:
    """When a user taps 'Watch movie' on a group movie card:
    - If user has never started the bot -> alert: 'Only bot users can see it. Start the bot...'
    - If movie is premium and user not premium -> alert: 'This movie is premium. Buy premium...'
    - If mandatory channels missing -> alert: 'Please join mandatory channels...'
    - If authorized bot user -> sends video to user's private chat and confirms with alert!"""
    movie_id = int(callback.data.split(":", 1)[1])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(DEFAULT_LANGUAGE, "movie_not_found"), show_alert=True)
        return

    tg_user = callback.from_user
    user = await uow.users.get_by_telegram_id(tg_user.id)

    # 1. Non-bot user:
    if user is None:
        await callback.answer(
            t(DEFAULT_LANGUAGE, "group_movie_not_bot_user"),
            show_alert=True,
        )
        return

    lang = user.language

    # 2. Movie is premium and user is not premium:
    if movie.access_type == MovieAccessType.PREMIUM.value and not user.is_premium_active:
        await callback.answer(
            t(lang, "group_movie_premium_required"),
            show_alert=True,
        )
        return

    # 3. Check access / mandatory channels
    checker = await _get_membership_checker(callback.bot, uow)
    access_service = MovieAccessService(uow, membership_checker=checker)
    decision = await access_service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    if not decision.allowed:
        if decision.reason == "premium_required":
            await callback.answer(
                t(lang, "group_movie_premium_required"),
                show_alert=True,
            )
            return
        await callback.answer(
            t(lang, "movie_must_join_channels"),
            show_alert=True,
        )
        return

    # 4. Authorized bot user: deliver video to private chat!
    video_file_id = await access_service.deliver_and_record_view(movie)
    caption = f"{movie.title(lang)}\n{t(lang, 'movie_code_label', code=movie.code)}"
    try:
        await callback.bot.send_video(chat_id=user.telegram_id, video=video_file_id, caption=caption)
        await callback.answer(t(lang, "group_movie_sent_to_pm"), show_alert=True)
    except Exception:
        await callback.answer(t(lang, "group_movie_not_bot_user"), show_alert=True)


async def send_movie_by_code(
    message: Message, *, uow: UnitOfWork, user: User | None, code: str
) -> None:
    movie = await uow.catalog.get_by_code(code)
    lang = user.language if user else DEFAULT_LANGUAGE
    if movie is None:
        await message.answer(t(lang, "movie_not_found"))
        return
    await _present_movie(message, uow, user, movie, bot=message.bot)


async def _present_movie(
    message: Message,
    uow: UnitOfWork,
    user: User | None,
    movie: Movie,
    *,
    bot,
    is_recheck: bool = False,
) -> None:
    is_group = message.chat.type in ("group", "supergroup")
    bot_username = get_settings().BOT_USERNAME.lstrip("@")
    deep_link = f"https://t.me/{bot_username}?start=movie_{movie.code}"

    # Handle group chats specially so non-bot users cannot view protected videos
    if is_group:
        # Case A: Requester is not a bot user (has never started the bot)
        if user is None:
            if movie.access_type == MovieAccessType.PREMIUM.value:
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=t(DEFAULT_LANGUAGE, "group_buy_premium_button"),
                                url=deep_link,
                            )
                        ]
                    ]
                )
                await message.reply(
                    t(DEFAULT_LANGUAGE, "group_movie_premium_required"),
                    reply_markup=markup,
                )
                return
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=t(DEFAULT_LANGUAGE, "group_start_bot_button"),
                            url=deep_link,
                        )
                    ]
                ]
            )
            await message.reply(
                t(DEFAULT_LANGUAGE, "group_movie_not_bot_user"),
                reply_markup=markup,
            )
            return

        lang = user.language

        # Case B: Requester is a bot user, but movie is premium and user is not premium
        if movie.access_type == MovieAccessType.PREMIUM.value and not user.is_premium_active:
            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=t(lang, "group_buy_premium_button"),
                            url=deep_link,
                        )
                    ]
                ]
            )
            await message.reply(
                t(lang, "group_movie_premium_required"),
                reply_markup=markup,
            )
            return

        # Case C: Check mandatory channels
        checker = await _get_membership_checker(bot, uow)
        access_service = MovieAccessService(uow, membership_checker=checker)
        decision = await access_service.check_access(
            user_id=user.id, telegram_id=user.telegram_id, movie=movie
        )

        if not decision.allowed:
            if decision.reason == "premium_required":
                markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text=t(lang, "group_buy_premium_button"),
                                url=deep_link,
                            )
                        ]
                    ]
                )
                await message.reply(
                    t(lang, "group_movie_premium_required"),
                    reply_markup=markup,
                )
                return
            channels = await uow.catalog.list_active_channels()
            relevant = [c for c in channels if c.chat_id in decision.missing_channels] or channels
            for ch in relevant:
                await ensure_channel_invite_link(bot, ch, uow)
            await message.reply(
                t(lang, "movie_must_join_channels"),
                reply_markup=join_channels_keyboard(relevant, movie.id, lang),
            )
            return

        # Case D: Bot user with full access!
        video_file_id = await access_service.deliver_and_record_view(movie)
        caption = f"{movie.title(lang)}\n{t(lang, 'movie_code_label', code=movie.code)}"

        # Send video directly to user's PM
        try:
            await bot.send_video(chat_id=user.telegram_id, video=video_file_id, caption=caption)
        except Exception:
            pass

        # Post the movie card in the group with interactive Watch button
        user_display = message.from_user.first_name if message.from_user else "Foydalanuvchi"
        card_text = t(
            lang,
            "group_movie_card",
            title=movie.title(lang),
            code=movie.code,
            user=user_display,
        )
        group_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=t(lang, "group_watch_button"),
                        callback_data=f"group_watch:{movie.id}",
                    ),
                    InlineKeyboardButton(
                        text=t(lang, "movie_open_in_bot_button"),
                        url=deep_link,
                    ),
                ]
            ]
        )
        await message.reply(card_text, reply_markup=group_markup)
        return

    # Private chat flow:
    lang = user.language if user else DEFAULT_LANGUAGE
    checker = await _get_membership_checker(bot, uow)
    access_service = MovieAccessService(uow, membership_checker=checker)
    uid = user.id if user else 0
    tid = user.telegram_id if user else (message.from_user.id if message.from_user else 0)
    decision = await access_service.check_access(user_id=uid, telegram_id=tid, movie=movie)

    if not decision.allowed:
        if decision.reason == "premium_required":
            await message.answer(t(lang, "movie_premium_required"))
            return
        if decision.reason in ("must_join_channels", "membership_check_unavailable"):
            channels = await uow.catalog.list_active_channels()
            relevant = [c for c in channels if c.chat_id in decision.missing_channels] or channels
            for ch in relevant:
                await ensure_channel_invite_link(bot, ch, uow)
            text_key = "movie_still_not_joined" if is_recheck else "movie_must_join_channels"
            await message.answer(
                t(lang, text_key),
                reply_markup=join_channels_keyboard(relevant, movie.id, lang),
            )
            return
        await message.answer(t(lang, "movie_not_found"))
        return

    video_file_id = await access_service.deliver_and_record_view(movie)
    caption = f"{movie.title(lang)}\n{t(lang, 'movie_code_label', code=movie.code)}"
    await message.answer_video(video=video_file_id, caption=caption)


@router.chat_join_request()
async def handle_chat_join_request(event: ChatJoinRequest, uow: UnitOfWork, **kwargs) -> None:
    """When a user sends a join request to a private channel/group:
    1. Record the join request in DB and Redis so the user is immediately accepted as followed.
    2. Attempt to approve the request if possible."""
    chat_id_str = str(event.chat.id)
    user_id = event.from_user.id

    await uow.catalog.record_join_request(chat_id_str, user_id)
    if event.chat.username:
        await uow.catalog.record_join_request(f"@{event.chat.username.lower()}", user_id)
    await uow.session.commit()

    try:
        redis = get_redis()
        await redis.set(f"cjr:{chat_id_str}:{user_id}", "1", ex=86400 * 30)
        if event.chat.username:
            await redis.set(f"cjr:@{event.chat.username.lower()}:{user_id}", "1", ex=86400 * 30)
    except Exception:
        pass

    try:
        await event.approve()
    except Exception:
        pass


@router.my_chat_member()
async def handle_my_chat_member(event: ChatMemberUpdated, uow: UnitOfWork, **kwargs) -> None:
    """When the bot is added to a channel/group and granted administrator rights:
    Automatically registers or activates the mandatory channel with a valid invite link."""
    if event.chat.type not in ("channel", "group", "supergroup"):
        return

    chat_id_str = str(event.chat.id)
    new_status = event.new_chat_member.status

    if new_status in ("administrator", "creator"):
        title = event.chat.title or "Channel"
        invite_link = None
        try:
            link_obj = await event.bot.create_chat_invite_link(chat_id=event.chat.id)
            invite_link = link_obj.invite_link
        except Exception:
            try:
                invite_link = await event.bot.export_chat_invite_link(chat_id=event.chat.id)
            except Exception:
                if event.chat.username:
                    invite_link = f"https://t.me/{event.chat.username}"

        channel = await uow.catalog.get_channel_by_chat_id(chat_id_str)
        if not channel and event.chat.username:
            channel = await uow.catalog.get_channel_by_chat_id(f"@{event.chat.username}")

        if channel:
            channel.title = title
            channel.bot_is_admin_verified = True
            channel.is_active = True
            if invite_link:
                channel.invite_link = invite_link
        else:
            channel = MandatoryChannel(
                chat_id=chat_id_str,
                title=title,
                invite_link=invite_link,
                is_active=True,
                bot_is_admin_verified=True,
            )
            uow.session.add(channel)
        await uow.session.commit()

    elif new_status in ("left", "kicked"):
        channel = await uow.catalog.get_channel_by_chat_id(chat_id_str)
        if channel:
            channel.bot_is_admin_verified = False
            channel.is_active = False
            await uow.session.commit()
