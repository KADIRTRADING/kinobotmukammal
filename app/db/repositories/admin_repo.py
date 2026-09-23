from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.admin import Admin, AuditLog
from app.db.models.enums import AdminRole


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> Admin | None:
        result = await self.session.execute(select(Admin).where(Admin.username == username))
        return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: int) -> Admin | None:
        result = await self.session.execute(select(Admin).where(Admin.id == admin_id))
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, telegram_id: int) -> Admin | None:
        result = await self.session.execute(select(Admin).where(Admin.telegram_id == telegram_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Admin:
        admin = Admin(**kwargs)
        self.session.add(admin)
        await self.session.flush()
        return admin

    async def count_admins(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(Admin.id)))
        return int(result.scalar_one())

    async def list_all(self) -> list[Admin]:
        result = await self.session.execute(select(Admin))
        return list(result.scalars().all())

    async def touch_login(self, admin: Admin) -> None:
        admin.last_login_at = dt.datetime.now(dt.UTC)
        await self.session.flush()

    async def list_notification_recipients(
        self, roles: list[AdminRole] | None = None
    ) -> list[Admin]:
        stmt = select(Admin).where(Admin.is_active.is_(True), Admin.telegram_id.is_not(None))
        if roles:
            stmt = stmt.where(Admin.role.in_([r.value for r in roles]))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(
        self,
        *,
        admin_id: int | None,
        admin_username: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        before: dict | None = None,
        after: dict | None = None,
        note: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        log = AuditLog(
            created_at=dt.datetime.now(dt.UTC),
            admin_id=admin_id,
            admin_username=admin_username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            note=note,
            ip_address=ip_address,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_recent(self, limit: int = 100) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
