"""Add admin_grants table: runtime-manageable in-Telegram admin access.

Lets an "owner" (a Telegram id listed in the TELEGRAM_SUPERADMIN_IDS env
var) grant/revoke admin-panel access to other Telegram accounts from
inside the bot itself, without editing `.env` or restarting any process.
See app/db/models/admin_grant.py and app/core/admin_access.py.

Revision ID: 0002_admin_grants
Revises: 0001_initial_schema
Create Date: 2026-09-24

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_admin_grants"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_grants",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("label", sa.String(256), nullable=True),
        sa.Column("granted_by_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("revoked_by_telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_unique_constraint("uq_admin_grants_telegram_id", "admin_grants", ["telegram_id"])
    op.create_index("ix_admin_grants_telegram_id", "admin_grants", ["telegram_id"])


def downgrade() -> None:
    op.drop_table("admin_grants")
