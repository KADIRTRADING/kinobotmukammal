"""Movie catalog: categories, movies, and mandatory subscription channels."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import MovieAccessType, MoviePublicationState


class Category(IdMixin, TimestampMixin, Base):
    __tablename__ = "categories"

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title_uz: Mapped[str] = mapped_column(String(128), nullable=False)
    title_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    title_en: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    movies: Mapped[list[Movie]] = relationship("Movie", back_populates="category")


class Movie(IdMixin, TimestampMixin, Base):
    __tablename__ = "movies"

    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    title_uz: Mapped[str] = mapped_column(String(256), nullable=False)
    title_ru: Mapped[str] = mapped_column(String(256), nullable=False)
    title_en: Mapped[str] = mapped_column(String(256), nullable=False)

    description_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Search index column (lower-cased concatenation of all titles), populated
    # by the repository layer on write for fast ILIKE / trigram search.
    search_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    poster_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    video_file_id: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        doc="Telegram file_id of the licensed source video. Never exposed to users.",
    )
    video_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    access_type: Mapped[MovieAccessType] = mapped_column(
        String(16), nullable=False, default=MovieAccessType.FREE.value
    )
    publication_state: Mapped[MoviePublicationState] = mapped_column(
        String(16), nullable=False, default=MoviePublicationState.DRAFT.value
    )

    view_count: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)

    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    category: Mapped[Category | None] = relationship("Category", back_populates="movies")

    def title(self, language: str) -> str:
        return {"uz": self.title_uz, "ru": self.title_ru, "en": self.title_en}.get(
            language, self.title_uz
        )

    def description(self, language: str) -> str | None:
        return {
            "uz": self.description_uz,
            "ru": self.description_ru,
            "en": self.description_en,
        }.get(language, self.description_uz)


class MandatoryChannel(IdMixin, TimestampMixin, Base):
    """A Telegram channel/group a FREE user must join before watching a FREE
    movie. Premium users are always exempt (checked in the service layer)."""

    __tablename__ = "mandatory_channels"

    chat_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, doc="Numeric chat id (-100...) or @username."
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    invite_link: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    bot_is_admin_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_checked_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


Index("ix_movies_category_id", Movie.category_id)
Index("ix_movies_publication_state", Movie.publication_state)
