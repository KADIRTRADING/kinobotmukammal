"""Group chat mention/reply filter middleware.

Enforces: In groups and supergroups, the bot will not reply to any message
unless someone explicitly mentions the bot or replies to a message sent by the bot.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, TelegramObject

from app.config import get_settings


class GroupMentionReplyMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._bot_username: str | None = None
        self._bot_id: int | None = None

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.chat.type in ("group", "supergroup"):
                bot: Bot = data.get("bot") or event.bot
                if self._bot_id is None and bot is not None:
                    self._bot_id = bot.id

                if self._bot_username is None and bot is not None:
                    try:
                        me = await bot.get_me()
                        self._bot_username = (me.username or "").lower().lstrip("@")
                    except Exception:
                        self._bot_username = get_settings().BOT_USERNAME.lower().lstrip("@")

                # 1. Reply to bot's message
                is_reply_to_bot = (
                    event.reply_to_message is not None
                    and event.reply_to_message.from_user is not None
                    and (
                        (self._bot_id is not None and event.reply_to_message.from_user.id == self._bot_id)
                        or event.reply_to_message.from_user.is_bot
                    )
                )

                # 2. Mention of the bot
                is_mentioned = False
                if not is_reply_to_bot:
                    entities = list(event.entities or []) + list(event.caption_entities or [])
                    text = event.text or event.caption or ""
                    for ent in entities:
                        if (
                            ent.type == "text_mention"
                            and ent.user
                            and self._bot_id is not None
                            and ent.user.id == self._bot_id
                        ):
                            is_mentioned = True
                            break
                        if ent.type in ("mention", "bot_command"):
                            segment = text[ent.offset : ent.offset + ent.length].lower()
                            if self._bot_username and f"@{self._bot_username}" in segment:
                                is_mentioned = True
                                break

                    if not is_mentioned and self._bot_username:
                        if f"@{self._bot_username}" in text.lower():
                            is_mentioned = True

                if not (is_reply_to_bot or is_mentioned):
                    # In groups, do not reply unless someone mentions or replies to bot
                    return None

        return await handler(event, data)
