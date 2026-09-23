"""Movie lookup + entitlement/subscription gating.

`MembershipChecker` is a small protocol so this service can be unit-tested
without a live Telegram connection; the real implementation (used by
handlers) calls `bot.get_chat_member` for each mandatory channel.

Critical invariant enforced here: `get_playable_movie` NEVER returns the
video_file_id unless access has just been verified in THIS call. Callers
(handlers) must not cache or forward the returned file_id anywhere a user
without access could retrieve it (this is also why inline search results
never include it -- see app/bot/handlers/inline_search.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.db.models.catalog import Movie
from app.db.models.enums import MovieAccessType, MoviePublicationState
from app.db.uow import UnitOfWork


class MembershipChecker(Protocol):
    async def __call__(self, telegram_id: int, chat_id: str) -> bool: ...


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str
    missing_channels: list[str]


class MovieAccessService:
    def __init__(
        self, uow: UnitOfWork, membership_checker: MembershipChecker | None = None
    ) -> None:
        self.uow = uow
        self._membership_checker = membership_checker

    async def find_by_code_or_search(self, query: str) -> list[Movie]:
        query = query.strip()
        exact = await self.uow.catalog.get_by_code(query)
        if exact and exact.publication_state == MoviePublicationState.PUBLISHED.value:
            return [exact]
        return await self.uow.catalog.search_published(query)

    async def check_access(self, *, user_id: int, telegram_id: int, movie: Movie) -> AccessDecision:
        if movie.publication_state != MoviePublicationState.PUBLISHED.value:
            return AccessDecision(False, "not_published", [])

        if movie.access_type == MovieAccessType.PREMIUM.value:
            user = await self.uow.users.get_by_id(user_id)
            if user and user.is_premium_active:
                return AccessDecision(True, "premium_access", [])
            return AccessDecision(False, "premium_required", [])

        # FREE movie: premium users are exempt from mandatory subscription
        # (spec section 2). Everyone else must have joined every active
        # mandatory channel.
        user = await self.uow.users.get_by_id(user_id)
        if user and user.is_premium_active:
            return AccessDecision(True, "premium_exempt", [])

        channels = await self.uow.catalog.list_active_channels()
        if not channels:
            return AccessDecision(True, "no_mandatory_channels", [])

        if self._membership_checker is None:
            # No live Telegram connection available (e.g. unit test) --
            # fail closed rather than silently granting access.
            return AccessDecision(
                False, "membership_check_unavailable", [c.chat_id for c in channels]
            )

        missing: list[str] = []
        for channel in channels:
            is_member = await self._membership_checker(telegram_id, channel.chat_id)
            if not is_member:
                missing.append(channel.chat_id)

        if missing:
            return AccessDecision(False, "must_join_channels", missing)
        return AccessDecision(True, "channels_joined", [])

    async def deliver_and_record_view(self, movie: Movie) -> str:
        """Returns the video_file_id ONLY after the caller has already
        confirmed `check_access(...).allowed is True` in the same request.
        Also increments the view counter."""
        await self.uow.catalog.increment_view_count(movie)
        return movie.video_file_id
