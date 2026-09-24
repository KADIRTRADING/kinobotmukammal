"""Runtime-manageable in-Telegram admin grants.

This table is what lets the main admin (whoever is listed in the
`TELEGRAM_SUPERADMIN_IDS` env var -- called an "owner" throughout this
codebase) grant panel access to OTHER Telegram accounts from inside the
bot itself, without editing `.env` or restarting any process.

Design notes (see also `app.core.admin_access`):
  - Owners (env `TELEGRAM_SUPERADMIN_IDS`) are the ONLY identities that can
    create or revoke a row here (enforced in
    `app.bot.handlers.admin.admins`, not in this model) -- a granted admin
    can use every other admin-panel section but can never grant/revoke
    another admin. This one-directional trust prevents a compromised or
    misbehaving granted admin from privilege-escalating by adding more
    admins of their own.
  - A row with `is_active=False` is kept (never deleted) so a revocation
    has a permanent, auditable history -- who granted it, who revoked it,
    and when. Re-granting the same Telegram id reactivates the existing
    row rather than creating a duplicate.
  - `telegram_id` is the ONLY identity carried here -- exactly like the
    env allowlist, there is no username/password for a granted admin
    either.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class AdminGrant(IdMixin, TimestampMixin, Base):
    __tablename__ = "admin_grants"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
        doc="Optional free-text note about who this is (e.g. '@username' or a name), "
        "purely for the admin list display -- never used for authorization.",
    )
    granted_by_telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="The owner's Telegram id who created/most-recently-reactivated this grant.",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revoked_by_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
