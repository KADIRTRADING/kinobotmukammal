"""Broadcasts: queued mass messages with per-recipient delivery tracking."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import BroadcastRecipientStatus, BroadcastStatus, BroadcastTarget


class Broadcast(IdMixin, TimestampMixin, Base):
    __tablename__ = "broadcasts"

    created_by_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    target: Mapped[BroadcastTarget] = mapped_column(String(16), nullable=False)
    target_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    custom_user_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)

    text_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    button_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    button_text: Mapped[str | None] = mapped_column(String(128), nullable=True)

    status: Mapped[BroadcastStatus] = mapped_column(
        String(16), nullable=False, default=BroadcastStatus.DRAFT.value
    )

    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rate_limit_per_second: Mapped[int] = mapped_column(Integer, nullable=False, default=20)

    scheduled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BroadcastRecipient(IdMixin, Base):
    __tablename__ = "broadcast_recipients"
    __table_args__ = (
        UniqueConstraint("broadcast_id", "user_id", name="uq_broadcast_recipients_broadcast_user"),
    )

    broadcast_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("broadcasts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[BroadcastRecipientStatus] = mapped_column(
        String(16), nullable=False, default=BroadcastRecipientStatus.PENDING.value
    )
    attempted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
