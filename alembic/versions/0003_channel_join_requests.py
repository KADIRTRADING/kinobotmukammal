"""Add channel_join_requests table.

Revision ID: 0003_channel_join_requests
Revises: 0002_admin_grants
Create Date: 2026-10-18
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_channel_join_requests"
down_revision: Union[str, None] = "0002_admin_grants"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "channel_join_requests",
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
        sa.Column("chat_id", sa.String(length=64), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
    )
    op.create_index(
        "ix_channel_join_requests_chat_id", "channel_join_requests", ["chat_id"]
    )
    op.create_index(
        "ix_channel_join_requests_telegram_id", "channel_join_requests", ["telegram_id"]
    )
    op.create_index(
        "ix_channel_join_requests_chat_user",
        "channel_join_requests",
        ["chat_id", "telegram_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("channel_join_requests")
