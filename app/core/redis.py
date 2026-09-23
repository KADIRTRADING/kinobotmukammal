"""Redis client factory.

Used for: FSM storage backing aiogram dialogs, rate limiting broadcast
sends, caching mandatory-channel membership checks briefly, and simple
distributed locks (e.g. preventing two workers from processing the same
scheduled job concurrently).
"""

from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from app.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.REDIS_URL, decode_responses=True)
