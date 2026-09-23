"""Blogger verification pipeline and blogger profile / reward configuration."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import BloggerApplicationStatus, BloggerProfileStatus

if TYPE_CHECKING:
    from app.db.models.user import User


class BloggerApplication(IdMixin, TimestampMixin, Base):
    """One row per blogger-verification attempt.

    Flow (spec section 5):
      1. applicant requests blogger status -> row created, status=PENDING,
         a unique `verification_phrase` is generated.
      2. applicant places the phrase in their social bio and submits
         `submitted_url`.
      3. admin reviews (manually, since arbitrary bio pages generally are not
         reachable through an authorized API) and approves/rejects with a
         reason.
    """

    __tablename__ = "blogger_applications"

    applicant_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    verification_phrase: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    platform_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    submitted_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    status: Mapped[BloggerApplicationStatus] = mapped_column(
        String(16), nullable=False, default=BloggerApplicationStatus.PENDING.value
    )

    auto_check_attempted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    auto_check_result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Human-readable outcome if an authorized platform API check ran; NULL if manual-only.",
    )

    reviewed_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    applicant: Mapped[User] = relationship("User", back_populates="blogger_applications")


class BloggerProfile(IdMixin, TimestampMixin, Base):
    """Created the moment an application is APPROVED. Holds blogger-specific
    reward configuration that can override the global per-1000 rate."""

    __tablename__ = "blogger_profiles"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    approved_application_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    status: Mapped[BloggerProfileStatus] = mapped_column(
        String(16), nullable=False, default=BloggerProfileStatus.ACTIVE.value
    )

    # NULL means "use the global default from settings".
    acquisition_reward_per_1000_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acquisition_reward_currency_override: Mapped[str | None] = mapped_column(
        String(8), nullable=True
    )

    approved_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    suspended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    suspension_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Running remainder (in minor units) carried forward so that
    # per-qualified-user fractional accrual never loses or overpays a
    # fraction of a minor unit. See app.services.blogger_rewards.
    accrual_remainder_micros: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, doc="Remainder expressed in millionths of a minor unit."
    )
    qualified_joins_counted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[User] = relationship("User", back_populates="blogger_profile")
