"""Resolves (or creates) the `User` row for the incoming Telegram sender and
injects it as `user` into handler data. Also enforces the blocked-user gate
here, in one place, instead of scattering `if user.is_blocked` checks
across every handler.

Must run AFTER `DbSessionMiddleware` (needs `data["uow"]`) and is
registered on both message and callback-query observer chains.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, Update

from app.db.uow import UnitOfWork
from app.i18n import DEFAULT_LANGUAGE, t


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = self._extract_from_user(event)
        if tg_user is None:
            return await handler(event, data)

        uow: UnitOfWork = data["uow"]
        user = await uow.users.get_by_telegram_id(tg_user.id)
        data["user"] = user
        data["language"] = user.language if user else DEFAULT_LANGUAGE

        if user is not None and user.is_blocked:
            await self._notify_blocked(event, user.language)
            return None  # short-circuit: blocked users never reach real handlers

        return await handler(event, data)

    @staticmethod
    def _extract_from_user(event: TelegramObject):
        if isinstance(event, Message):
            return event.from_user
        if isinstance(event, CallbackQuery):
            return event.from_user
        if isinstance(event, Update):
            inner = event.message or event.callback_query or event.inline_query
            return inner.from_user if inner else None
        return getattr(event, "from_user", None)

    @staticmethod
    async def _notify_blocked(event: TelegramObject, language: str) -> None:
        text = t(language, "error_blocked_user")
        try:
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
        except Exception:
            pass
