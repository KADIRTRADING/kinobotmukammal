"""One-off CLI to create the first SUPERADMIN account.

Usage (see README "First run"):
    python -m scripts.create_superadmin --username admin --password 'change-me-now'

Run this once after migrations. There is no self-registration UI for the
admin panel by design -- every subsequent admin account is created by an
existing SUPERADMIN through the (future) admin-management screen or by
running this script again with a different username.
"""

from __future__ import annotations

import argparse
import asyncio

from app.admin.security import hash_password
from app.db.models.enums import AdminRole
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork


async def main(username: str, password: str, telegram_id: int | None) -> None:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        existing = await uow.admins.get_by_username(username)
        if existing is not None:
            print(f"Admin '{username}' already exists (id={existing.id}). Nothing to do.")
            return
        admin = await uow.admins.create(
            username=username,
            password_hash=hash_password(password),
            telegram_id=telegram_id,
            role=AdminRole.SUPERADMIN.value,
            is_active=True,
        )
        await session.commit()
        print(f"Created SUPERADMIN '{username}' (id={admin.id}).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the first SUPERADMIN account")
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "--telegram-id",
        type=int,
        default=None,
        help="Optional: enables Telegram admin notifications",
    )
    args = parser.parse_args()
    asyncio.run(main(args.username, args.password, args.telegram_id))
