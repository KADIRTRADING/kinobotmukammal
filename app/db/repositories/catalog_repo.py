from __future__ import annotations

from sqlalchemy import func, select
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

    async def list_all_categories(self) -> list[Category]:
        """Unlike `list_active_categories`, includes disabled categories --
        used by the admin panel, which must be able to see and re-enable a
        disabled category."""
        stmt = select(Category).order_by(Category.sort_order)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_category(self, category_id: int) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_category_by_slug(self, slug: str) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.slug == slug))
        return result.scalar_one_or_none()

    async def create_category(self, **kwargs) -> Category:
        if "sort_order" not in kwargs:
            max_sort = await self.session.execute(select(func.max(Category.sort_order)))
            current_max = max_sort.scalar_one_or_none() or 0
            kwargs["sort_order"] = current_max + 1
        category = Category(**kwargs)
        self.session.add(category)
        await self.session.flush()
        return category

    async def update_category(self, category: Category, **kwargs) -> Category:
        for k, v in kwargs.items():
            setattr(category, k, v)
        await self.session.flush()
        return category

    async def swap_category_sort_order(self, category_a: Category, category_b: Category) -> None:
        """Atomically swaps two categories' `sort_order` values -- used by
        the admin panel's up/down reordering buttons. Both rows are already
        attached to `self.session`, so this is a single flush."""
        category_a.sort_order, category_b.sort_order = category_b.sort_order, category_a.sort_order
        await self.session.flush()

    async def get_category_neighbor(self, category: Category, *, direction: str) -> Category | None:
        """Returns the category immediately above (`direction="up"`) or
        below (`direction="down"`) `category` in sort order, or None if
        `category` is already at that end of the list."""
        stmt = select(Category).order_by(Category.sort_order)
        if direction == "up":
            stmt = stmt.where(Category.sort_order < category.sort_order).order_by(
                Category.sort_order.desc()
            )
        else:
            stmt = stmt.where(Category.sort_order > category.sort_order).order_by(
                Category.sort_order.asc()
            )
        result = await self.session.execute(stmt.limit(1))
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

    async def delete(self, movie: Movie) -> None:
        """Hard delete, used only by the admin "Delete" action after an
        explicit confirmation step (see spec: "Show confirmation before
        deletion"). Publishing/archiving (see `update`) is preferred for
        normal lifecycle management since it preserves `view_count` and any
        `Entitlement`/order history that might reference this movie's
        catalog metadata; delete is for genuine mistakes (wrong upload,
        wrong code, etc.)."""
        await self.session.delete(movie)
        await self.session.flush()

    async def list_all_movies(self, limit: int = 1000, offset: int = 0) -> list[Movie]:
        """Unlike `list_by_category`/`search_published`, includes movies in
        every publication state (draft/published/archived) -- used by the
        admin panel's movie list, which must show drafts too."""
        stmt = select(Movie).order_by(Movie.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_movies(self) -> int:
        result = await self.session.execute(select(func.count(Movie.id)))
        return int(result.scalar_one())

    async def search_any_state(self, query: str, limit: int = 15) -> list[Movie]:
        """Like `search_published`, but matches movies in ANY publication
        state -- used by the admin panel's "search by code" action, which
        must be able to find a draft an admin hasn't published yet."""
        q = query.strip().lower()
        stmt = (
            select(Movie)
            .where(Movie.search_text.ilike(f"%{q}%"))
            .order_by(Movie.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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

    async def get_channel(self, channel_id: int) -> MandatoryChannel | None:
        result = await self.session.execute(
            select(MandatoryChannel).where(MandatoryChannel.id == channel_id)
        )
        return result.scalar_one_or_none()

    async def get_channel_by_chat_id(self, chat_id: str) -> MandatoryChannel | None:
        result = await self.session.execute(
            select(MandatoryChannel).where(MandatoryChannel.chat_id == chat_id)
        )
        return result.scalar_one_or_none()

    async def create_channel(self, **kwargs) -> MandatoryChannel:
        channel = MandatoryChannel(**kwargs)
        self.session.add(channel)
        await self.session.flush()
        return channel

    async def update_channel(self, channel: MandatoryChannel, **kwargs) -> MandatoryChannel:
        for k, v in kwargs.items():
            setattr(channel, k, v)
        await self.session.flush()
        return channel

    async def delete_channel(self, channel: MandatoryChannel) -> None:
        """Hard delete -- used by the admin "Remove" action. Unlike movies
        (which are archived, never deleted, to preserve view-count history
        and past entitlement references), a mandatory channel carries no
        historical financial data, so a hard delete is safe and matches
        what an admin expects "remove" to mean here."""
        await self.session.delete(channel)
        await self.session.flush()
