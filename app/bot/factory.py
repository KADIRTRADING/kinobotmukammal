"""Builds the aiogram `Bot` + `Dispatcher`, wiring middlewares and handlers.

Used by both `app.main` (long-polling / webhook entrypoint) and
`app.api.webhooks.telegram` (feeding updates from the FastAPI webhook route
into the same Dispatcher when `BOT_WEBHOOK_URL` is configured).
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from app.bot.handlers import register_all
from app.bot.middlewares.db_session import DbSessionMiddleware
from app.bot.middlewares.user_context import UserContextMiddleware
from app.config import Settings, get_settings
from app.core.redis import get_redis


def build_bot(settings: Settings | None = None) -> Bot:
    settings = settings or get_settings()
    return Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def build_dispatcher(settings: Settings | None = None) -> Dispatcher:
    settings = settings or get_settings()
    storage = RedisStorage(redis=get_redis())
    dp = Dispatcher(storage=storage)

    # Order matters: DB session must be opened before user context resolves.
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.outer_middleware(UserContextMiddleware())

    register_all(dp)
    return dp
