"""Shared helper for recording admin audit-log entries from Telegram admin
handlers.

There is no `Admin` DB row for Telegram-native admins (per design: no
username/password, no `scripts/create_superadmin.py` step is required to
activate admin access -- see `app.core.admin_access`). Audit entries
therefore identify the actor by their Telegram numeric id, stored in
`AuditLog.admin_username` as `"tg:<id>"`, with `admin_id` left NULL. This
keeps every sensitive admin action traceable to a specific real Telegram
account without inventing a fake `Admin` row for it.
"""

from __future__ import annotations

from app.db.models.user import User
from app.db.uow import UnitOfWork


async def record_admin_action(
    uow: UnitOfWork,
    actor: User,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    note: str | None = None,
) -> None:
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{actor.telegram_id}",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
        note=note,
    )
