from __future__ import annotations

import datetime as dt
import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User

_REFERRAL_ALPHABET = string.ascii_letters + string.digits


def generate_referral_code(length: int = 10) -> str:
    return "".join(secrets.choice(_REFERRAL_ALPHABET) for _ in range(length))


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, code: str) -> User | None:
        result = await self.session.execute(select(User).where(User.referral_code == code))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.username == username.lstrip("@"))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language: str,
    ) -> User:
        now = dt.datetime.now(dt.UTC)
        code = generate_referral_code()
        # Extremely unlikely collision, but guard anyway.
        while await self.get_by_referral_code(code) is not None:
            code = generate_referral_code()

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language=language,
            language_selected=False,
            referral_code=code,
            started_at=now,
            last_seen_at=now,
            start_count=1,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def touch_start(self, user: User) -> None:
        user.last_seen_at = dt.datetime.now(dt.UTC)
        user.start_count += 1
        await self.session.flush()

    async def set_language(self, user: User, language: str) -> None:
        user.language = language
        user.language_selected = True
        await self.session.flush()

    async def set_blocked(self, user: User, blocked: bool, reason: str | None = None) -> None:
        user.is_blocked = blocked
        user.block_reason = reason
        await self.session.flush()

    async def search_by_name_or_id(
        self, query: str, limit: int = 20, offset: int = 0
    ) -> list[User]:
        if query.isdigit():
            stmt = select(User).where(User.telegram_id == int(query)).limit(limit).offset(offset)
        elif query:
            like = f"%{query.lower()}%"
            stmt = (
                select(User)
                .where(
                    (User.username.ilike(like))
                    | (User.first_name.ilike(like))
                    | (User.last_name.ilike(like))
                )
                .order_by(User.id)
                .limit(limit)
                .offset(offset)
            )
        else:
            stmt = select(User).order_by(User.id).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_search_by_name_or_id(self, query: str) -> int:
        from sqlalchemy import func

        if query.isdigit():
            stmt = select(func.count(User.id)).where(User.telegram_id == int(query))
        elif query:
            like = f"%{query.lower()}%"
            stmt = select(func.count(User.id)).where(
                (User.username.ilike(like))
                | (User.first_name.ilike(like))
                | (User.last_name.ilike(like))
            )
        else:
            stmt = select(func.count(User.id))
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def count_all(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(User.id)))
        return int(result.scalar_one())

    async def count_active_since(self, since: dt.datetime) -> int:
        """Number of users whose `last_seen_at` (updated on every /start,
        see `touch_start`) falls on or after `since` -- used by the admin
        dashboard's "active users" metric (spec: "active users")."""
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(User.id)).where(User.last_seen_at >= since)
        )
        return int(result.scalar_one())

    async def grant_premium_until(self, user: User, until: dt.datetime) -> None:
        # Extend, never shorten, an existing active entitlement window.
        if user.premium_until and user.premium_until > until:
            return
        user.premium_until = until
        await self.session.flush()

    async def iter_broadcast_targets(
        self, *, language: str | None = None, premium_only: bool | None = None
    ):
        stmt = select(User).where(User.is_blocked.is_(False), User.is_bot_blocked.is_(False))
        if language:
            stmt = stmt.where(User.language == language)
        if premium_only is True:
            stmt = stmt.where(
                User.premium_until.is_not(None), User.premium_until > dt.datetime.now(dt.UTC)
            )
        elif premium_only is False:
            stmt = stmt.where(
                (User.premium_until.is_(None)) | (User.premium_until <= dt.datetime.now(dt.UTC))
            )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
