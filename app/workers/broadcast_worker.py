"""Sends queued broadcasts in rate-limited batches, resumable across
restarts (progress is tracked per-recipient in the DB, not in memory).

Never blocks a bot handler or admin HTTP request -- this runs on its own
schedule in `app.workers.runner`, polling for QUEUED/RUNNING broadcasts.
"""

from __future__ import annotations

import asyncio

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from app.core.logging import get_logger
from app.db.models.enums import BroadcastRecipientStatus, BroadcastStatus
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork

logger = get_logger(__name__)

BATCH_SIZE = 200


async def process_pending_broadcasts(bot: Bot) -> None:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        broadcasts = await uow.broadcasts.list_queued_or_running()

    for broadcast in broadcasts:
        await _process_one_broadcast(bot, broadcast.id)


async def _process_one_broadcast(bot: Bot, broadcast_id: int) -> None:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        broadcast = await uow.broadcasts.lock(broadcast_id)
        if broadcast is None or broadcast.status == BroadcastStatus.CANCELLED.value:
            return
        if broadcast.status == BroadcastStatus.QUEUED.value:
            await uow.broadcasts.update_status(broadcast, BroadcastStatus.RUNNING)
        await session.commit()

    delay = 1.0 / max(broadcast.rate_limit_per_second, 1)

    while True:
        async with AsyncSessionLocal() as session:
            uow = UnitOfWork(session)
            broadcast = await uow.broadcasts.get(broadcast_id)
            if broadcast is None or broadcast.status == BroadcastStatus.CANCELLED.value:
                return
            recipients = await uow.broadcasts.list_pending_recipients(
                broadcast_id, limit=BATCH_SIZE
            )
            if not recipients:
                await uow.broadcasts.update_status(broadcast, BroadcastStatus.COMPLETED)
                await session.commit()
                return

            for recipient in recipients:
                user = await uow.users.get_by_id(recipient.user_id)
                if user is None or user.is_blocked or user.is_bot_blocked:
                    await uow.broadcasts.mark_recipient(recipient, BroadcastRecipientStatus.SKIPPED)
                    await uow.broadcasts.increment_counters(broadcast, skipped=1)
                    continue

                text = {
                    "uz": broadcast.text_uz,
                    "ru": broadcast.text_ru,
                    "en": broadcast.text_en,
                }.get(user.language, broadcast.text_uz)
                try:
                    if broadcast.photo_file_id:
                        await bot.send_photo(
                            chat_id=user.telegram_id, photo=broadcast.photo_file_id, caption=text
                        )
                    else:
                        await bot.send_message(chat_id=user.telegram_id, text=text)
                    await uow.broadcasts.mark_recipient(recipient, BroadcastRecipientStatus.SENT)
                    await uow.broadcasts.increment_counters(broadcast, sent=1)
                except TelegramForbiddenError:
                    user.is_bot_blocked = True
                    await uow.broadcasts.mark_recipient(
                        recipient, BroadcastRecipientStatus.FAILED, error="bot_blocked"
                    )
                    await uow.broadcasts.increment_counters(broadcast, failed=1)
                except TelegramRetryAfter as exc:
                    await asyncio.sleep(exc.retry_after)
                    await uow.broadcasts.mark_recipient(recipient, BroadcastRecipientStatus.PENDING)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Broadcast send failed for user %s: %s", user.telegram_id, exc)
                    await uow.broadcasts.mark_recipient(
                        recipient, BroadcastRecipientStatus.FAILED, error=str(exc)
                    )
                    await uow.broadcasts.increment_counters(broadcast, failed=1)

                await asyncio.sleep(delay)

            await session.commit()
