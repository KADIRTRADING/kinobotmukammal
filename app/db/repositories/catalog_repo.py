from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import Category, ChannelJoinRequest, MandatoryChannel, Movie
from app.db.models.enums import MoviePublicationState


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Categories -------------------------------------------------------------
    async def list_active_categories(self) -> list[Category]:
        stmt = select(Category).where(Category.is_active.is_(True)).order_by(Category.sort_order)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_category(self, category_id: int) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    # --- Movies ----------------------------------------------------------------
    async def get_by_code(self, code: str) -> Movie | None:
        result = await self.session.execute(select(Movie).where(Movie.code == code))
        return result.scalar_one_or_none()

    async def get_by_id(self, movie_id: int) -> Movie | None:
        result = await self.session.execute(select(Movie).where(Movie.id == movie_id))
        return result.scalar_one_or_none()

    async def search_published(self, query: str, limit: int = 15) -> list[Movie]:
        """Exact-title or partial-title search, scoped to published movies only.
        Never matches codes -- codes require full exact match via get_by_code."""
        published = MoviePublicationState.PUBLISHED.value
        q = query.strip().lower()
        stmt = (
            select(Movie)
            .where(Movie.publication_state == published)
            .where(
                or_(
                    Movie.title_uz.ilike(f"%{q}%"),
                    Movie.title_ru.ilike(f"%{q}%"),
                    Movie.title_en.ilike(f"%{q}%"),
                )
            )
            .order_by(Movie.view_count.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_category(
        self, category_id: int, limit: int = 30, offset: int = 0
    ) -> list[Movie]:
        stmt = (
            select(Movie)
            .where(
                Movie.category_id == category_id,
                Movie.publication_state == MoviePublicationState.PUBLISHED.value,
            )
            .order_by(Movie.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> Movie:
        movie = Movie(**kwargs)
        movie.search_text = self._build_search_text(movie)
        self.session.add(movie)
        await self.session.flush()
        return movie

    async def update(self, movie: Movie, **kwargs) -> Movie:
        for k, v in kwargs.items():
            setattr(movie, k, v)
        movie.search_text = self._build_search_text(movie)
        await self.session.flush()
        return movie

    async def increment_view_count(self, movie: Movie) -> None:
        movie.view_count += 1
        await self.session.flush()

    @staticmethod
    def _build_search_text(movie: Movie) -> str:
        parts = [movie.title_uz, movie.title_ru, movie.title_en]
        return " | ".join(p.lower() for p in parts if p)

    # --- Mandatory channels ------------------------------------------------------
    async def list_active_channels(self) -> list[MandatoryChannel]:
        result = await self.session.execute(
            select(MandatoryChannel).where(MandatoryChannel.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def list_all_channels(self) -> list[MandatoryChannel]:
        result = await self.session.execute(select(MandatoryChannel))
        return list(result.scalars().all())

    async def get_channel_by_chat_id(self, chat_id: str) -> MandatoryChannel | None:
        cid = str(chat_id).strip()
        result = await self.session.execute(
            select(MandatoryChannel).where(MandatoryChannel.chat_id == cid)
        )
        return result.scalar_one_or_none()

    async def update_channel_invite_link(
        self, channel: MandatoryChannel, invite_link: str
    ) -> MandatoryChannel:
        channel.invite_link = invite_link
        await self.session.flush()
        return channel

    # --- Channel join requests ---------------------------------------------------
    async def record_join_request(self, chat_id: str, telegram_id: int) -> ChannelJoinRequest:
        cid = str(chat_id).strip()
        stmt = select(ChannelJoinRequest).where(
            ChannelJoinRequest.chat_id == cid,
            ChannelJoinRequest.telegram_id == telegram_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing
        cjr = ChannelJoinRequest(chat_id=cid, telegram_id=telegram_id)
        self.session.add(cjr)
        await self.session.flush()
        return cjr

    async def has_join_request(self, chat_id: str, telegram_id: int) -> bool:
        cid = str(chat_id).strip()
        stmt = select(ChannelJoinRequest.id).where(
            ChannelJoinRequest.chat_id == cid,
            ChannelJoinRequest.telegram_id == telegram_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none() is not None

    async def delete(self, movie: Movie) -> None:
        await self.session.delete(movie)
        await self.session.flush()

    async def list_all_movies(self, limit: int = 200, offset: int = 0) -> list[Movie]:
        stmt = select(Movie).order_by(Movie.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_channel(self, channel: MandatoryChannel) -> None:
        await self.session.delete(channel)
        await self.session.flush()

    async def count_movies(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(Movie.id)))
        return int(result.scalar_one())

    async def count_channels(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(MandatoryChannel.id)))
        return int(result.scalar_one())
