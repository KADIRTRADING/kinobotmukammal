from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import BloggerStatusCache, Language

if TYPE_CHECKING:
    from app.db.models.blogger import BloggerApplication, BloggerProfile
    from app.db.models.referral import Referral
    from app.db.models.wallet import Wallet


class User(IdMixin, TimestampMixin, Base):
    """A Telegram end user of the bot.

    `telegram_id` is the stable Telegram numeric user id and is what every
    other table references. The surrogate `id` exists purely for compact FK
    storage and is never shown to end users.
    """

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(256), nullable=True)

    language: Mapped[Language] = mapped_column(String(8), nullable=False, default=Language.UZ.value)
    language_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_bot_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="True if the user blocked the bot (delivery failed).",
    )
    block_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)

    referred_by_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    referral_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)

    blogger_status_cache: Mapped[BloggerStatusCache] = mapped_column(
        String(16), nullable=False, default=BloggerStatusCache.NONE.value
    )

    premium_until: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=1,
        doc="How many times /start was issued; used for fraud heuristics.",
    )

    referred_by: Mapped[User | None] = relationship(
        "User", remote_side="User.id", foreign_keys=[referred_by_user_id]
    )
    wallets: Mapped[list[Wallet]] = relationship(
        "Wallet", back_populates="user", cascade="all, delete-orphan"
    )
    blogger_profile: Mapped[BloggerProfile | None] = relationship(
        "BloggerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    blogger_applications: Mapped[list[BloggerApplication]] = relationship(
        "BloggerApplication", back_populates="applicant", cascade="all, delete-orphan"
    )
    referral_as_referred: Mapped[Referral | None] = relationship(
        "Referral",
        back_populates="referred_user",
        uselist=False,
        foreign_keys="Referral.referred_user_id",
    )

    @property
    def is_premium_active(self) -> bool:
        if self.premium_until is None:
            return False
        return self.premium_until > dt.datetime.now(dt.UTC)

    def __repr__(self) -> str:  # pragma: no cover - debug helper only
        return f"<User id={self.id} tg={self.telegram_id} lang={self.language}>"


Index("ix_users_referred_by_user_id", User.referred_by_user_id)
