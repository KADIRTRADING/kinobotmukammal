from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.settings import Setting


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, key: str) -> str | None:
        result = await self.session.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        return row.value if row else None

    async def get_int(self, key: str, default: int) -> int:
        value = await self.get(key)
        return int(value) if value is not None else default

    async def get_bool(self, key: str, default: bool) -> bool:
        value = await self.get(key)
        if value is None:
            return default
        return value.strip().lower() in ("true", "1", "yes", "on")

    async def set(self, key: str, value: str, description: str | None = None) -> Setting:
        result = await self.session.execute(select(Setting).where(Setting.key == key))
        row = result.scalar_one_or_none()
        if row is None:
            row = Setting(key=key, value=value, description=description)
            self.session.add(row)
        else:
            row.value = value
            if description:
                row.description = description
        await self.session.flush()
        return row

    async def list_all(self) -> list[Setting]:
        result = await self.session.execute(select(Setting))
        return list(result.scalars().all())
