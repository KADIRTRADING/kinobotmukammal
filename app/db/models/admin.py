from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import AdminRole


class Admin(IdMixin, TimestampMixin, Base):
    """Administrative / staff account.

    Admins authenticate to the web admin panel with a username + password
    (bcrypt hash). Telegram admin notifications are sent to `telegram_id`
    when set, independent of web-login capability.
    """

    __tablename__ = "admins"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    role: Mapped[AdminRole] = mapped_column(
        String(16), nullable=False, default=AdminRole.MODERATOR.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AuditLog(IdMixin, Base):
    """Immutable append-only record of every sensitive admin action.

    Never updated or deleted; only inserted. `before`/`after` are JSON
    snapshots of the affected entity to support after-the-fact review.
    """

    __tablename__ = "audit_logs"

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    admin_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
