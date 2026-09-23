"""Catch-all text router. MUST be included LAST in `register_all` so every
menu-button router and every active FSM state gets first refusal; anything
that reaches this handler is treated as a movie code/name search query,
matching spec section 2 ("Enter a movie code", "type the movie's complete
name", "search by a partial name").
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.bot.handlers.movies import handle_movie_query_text
from app.db.models.user import User
from app.db.uow import UnitOfWork

router = Router(name="fallback_text")


@router.message(F.text)
async def handle_fallback_text(message: Message, uow: UnitOfWork, user: User, **kwargs) -> None:
    if user is None:
        return
    await handle_movie_query_text(message, uow, user)
