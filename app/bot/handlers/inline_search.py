"""Inline mode: `@YourBot 222` in any chat returns a safe movie card.

Privacy/security invariant (spec section 2): the returned
`InlineQueryResultArticle` NEVER contains the movie's `video_file_id` and
NEVER embeds it in the "Open in Bot" URL -- it only carries the movie's
CODE, which is not secret (codes are how users normally look movies up)
and does not by itself grant access. The actual entitlement/mandatory-
channel check happens only in `app.bot.handlers.movies._present_movie`,
triggered by the `?start=movie_<code>` deep link from the "Open in Bot"
button, after the user opens a PRIVATE chat with the bot. A group chat
member other than the requester can see the card but tapping it just opens
their OWN private chat with the bot and their OWN access is checked --
nobody else's protected video is ever exposed through the inline result
itself.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from app.config import get_settings
from app.db.uow import UnitOfWork
from app.i18n import DEFAULT_LANGUAGE, t
from app.services.movie_access_service import MovieAccessService

router = Router(name="inline_search")

_settings = get_settings()


@router.inline_query()
async def handle_inline_query(inline_query: InlineQuery, uow: UnitOfWork, **kwargs) -> None:
    query = inline_query.query.strip()
    if not query:
        await inline_query.answer([], cache_time=1)
        return

    language = DEFAULT_LANGUAGE
    user = await uow.users.get_by_telegram_id(inline_query.from_user.id)
    if user is not None:
        language = user.language

    access_service = MovieAccessService(uow)
    movies = await access_service.find_by_code_or_search(query)

    results = []
    for movie in movies[:20]:
        deep_link = f"https://t.me/{_settings.BOT_USERNAME}?start=movie_{movie.code}"
        results.append(
            InlineQueryResultArticle(
                id=str(movie.id),
                title=t(
                    language,
                    "movie_inline_card_title",
                    title=movie.title(language),
                    code=movie.code,
                ),
                description=movie.description(language) or "",
                thumbnail_url=None,
                input_message_content=InputTextMessageContent(
                    message_text=t(language, "movie_inline_card_description")
                ),
                reply_markup=_open_in_bot_markup(deep_link, language),
            )
        )

    await inline_query.answer(results, cache_time=30, is_personal=True)


def _open_in_bot_markup(deep_link: str, language: str):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(language, "movie_open_in_bot_button"), url=deep_link)]
        ]
    )
