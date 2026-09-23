"""Telegram webhook endpoint.

Only mounted/relevant when `BOT_WEBHOOK_URL` is configured (otherwise
`app.main` runs the bot via long polling and this route is never hit in
practice, though it stays registered and harmless). Verifies the
`X-Telegram-Bot-Api-Secret-Token` header against `BOT_WEBHOOK_SECRET`
before doing anything else -- this is the ONLY authentication Telegram
webhooks offer, and skipping it would let anyone forge bot updates.
"""

from __future__ import annotations

from aiogram import Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, Response

from app.config import get_settings

router = APIRouter(prefix="/webhooks/telegram", tags=["telegram-webhook"])
settings = get_settings()


@router.post("")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> Response:
    if x_telegram_bot_api_secret_token != settings.BOT_WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret token")

    dp: Dispatcher = request.app.state.dispatcher
    bot = request.app.state.bot

    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot=bot, update=update)
    return Response(status_code=200)
