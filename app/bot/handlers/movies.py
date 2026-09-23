"""Movie search, category browsing, mandatory-channel gating, and delivery.

`send_movie_by_code` is the single function that ever calls
`MovieAccessService.deliver_and_record_view` (which returns the raw
`video_file_id`); it is invoked from here AND from `start.py`'s deep-link
handler AND from the inline-search "Open in Bot" flow, so there is exactly
one code path that can hand a protected video to a user.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.movies import (
    category_list_keyboard,
    join_channels_keyboard,
    movie_search_results_keyboard,
)
from app.db.models.catalog import Movie
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import SUPPORTED_LANGUAGES, t
from app.services.movie_access_service import MovieAccessService

router = Router(name="movies")


def _menu_texts(key: str) -> set[str]:
    """All localized variants of a menu button's label, used as an aiogram
    `F.text.in_(...)` filter so the same handler matches regardless of the
    user's chosen language."""
    return {t(lang, key) for lang in SUPPORTED_LANGUAGES}


async def _get_membership_checker(bot):
    async def checker(telegram_id: int, chat_id: str) -> bool:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=telegram_id)
            return member.status in ("member", "administrator", "creator")
        except Exception:
            return False

    return checker


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


async def handle_movie_query_text(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    """Called by `app.bot.handlers.fallback_text`'s catch-all router, which
    is registered LAST in `register_all` so every other feature router
    (premium/wallet/promo/gifts/support/settings menu buttons, FSM text
    steps) gets first refusal on a text message. Anything that reaches here
    is treated as a movie code/name search query."""
    access_service = MovieAccessService(uow)
    results = await access_service.find_by_code_or_search(message.text)
    if not results:
        await message.answer(t(user.language, "movie_not_found"))
        return
    if len(results) == 1:
        await _present_movie(message, uow, user, results[0], bot=message.bot)
        return
    await message.answer(
        t(user.language, "movie_search_results"),
        reply_markup=movie_search_results_keyboard(results, user.language),
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
    movie_id = int(callback.data.split(":", 1)[1])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "movie_not_found"), show_alert=True)
        return
    await _present_movie(callback.message, uow, user, movie, bot=callback.bot, is_recheck=True)
    await callback.answer()


async def send_movie_by_code(message: Message, *, uow: UnitOfWork, user: User, code: str) -> None:
    movie = await uow.catalog.get_by_code(code)
    if movie is None:
        await message.answer(t(user.language, "movie_not_found"))
        return
    await _present_movie(message, uow, user, movie, bot=message.bot)


async def _present_movie(
    message: Message, uow: UnitOfWork, user: User, movie: Movie, *, bot, is_recheck: bool = False
) -> None:
    checker = await _get_membership_checker(bot)
    access_service = MovieAccessService(uow, membership_checker=checker)
    decision = await access_service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    if not decision.allowed:
        if decision.reason == "premium_required":
            await message.answer(t(user.language, "movie_premium_required"))
            return
        if decision.reason in ("must_join_channels", "membership_check_unavailable"):
            channels = await uow.catalog.list_active_channels()
            relevant = [c for c in channels if c.chat_id in decision.missing_channels] or channels
            text_key = "movie_still_not_joined" if is_recheck else "movie_must_join_channels"
            await message.answer(
                t(user.language, text_key),
                reply_markup=join_channels_keyboard(relevant, movie.id, user.language),
            )
            return
        await message.answer(t(user.language, "movie_not_found"))
        return

    video_file_id = await access_service.deliver_and_record_view(movie)
    caption = (
        f"{movie.title(user.language)}\n{t(user.language, 'movie_code_label', code=movie.code)}"
    )
    await message.answer_video(video=video_file_id, caption=caption)
