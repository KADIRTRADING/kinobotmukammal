"""Opens one DB transaction (UnitOfWork) per incoming Telegram update and
commits it after the handler returns, rolling back on any exception. Every
handler receives `uow: UnitOfWork` in its keyword arguments via this
middleware -- no handler ever opens its own session.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with AsyncSessionLocal() as session:
            uow = UnitOfWork(session)
            data["uow"] = uow
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
