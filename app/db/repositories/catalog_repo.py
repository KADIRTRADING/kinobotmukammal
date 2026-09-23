from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import Category, MandatoryChannel, Movie
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
        """Exact code match, exact-title match, or partial-title search, all
        scoped to published movies only (drafts/archived never surface to
        end users)."""
        published = MoviePublicationState.PUBLISHED.value
        q = query.strip().lower()
        stmt = (
            select(Movie)
            .where(Movie.publication_state == published)
            .where(Movie.search_text.ilike(f"%{q}%"))
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
        parts = [movie.code, movie.title_uz, movie.title_ru, movie.title_en]
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
