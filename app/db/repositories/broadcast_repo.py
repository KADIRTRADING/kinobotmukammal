from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.broadcast import Broadcast, BroadcastRecipient
from app.db.models.enums import BroadcastRecipientStatus, BroadcastStatus


class BroadcastRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Broadcast:
        broadcast = Broadcast(**kwargs)
        self.session.add(broadcast)
        await self.session.flush()
        return broadcast

    async def get(self, broadcast_id: int) -> Broadcast | None:
        result = await self.session.execute(select(Broadcast).where(Broadcast.id == broadcast_id))
        return result.scalar_one_or_none()

    async def lock(self, broadcast_id: int) -> Broadcast | None:
        stmt = select(Broadcast).where(Broadcast.id == broadcast_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_recipients(self, broadcast_id: int, user_ids: list[int]) -> None:
        self.session.add_all(
            [BroadcastRecipient(broadcast_id=broadcast_id, user_id=uid) for uid in user_ids]
        )
        await self.session.flush()

    async def list_pending_recipients(
        self, broadcast_id: int, limit: int = 200
    ) -> list[BroadcastRecipient]:
        stmt = (
            select(BroadcastRecipient)
            .where(
                BroadcastRecipient.broadcast_id == broadcast_id,
                BroadcastRecipient.status == BroadcastRecipientStatus.PENDING.value,
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_recipient(
        self,
        recipient: BroadcastRecipient,
        status: BroadcastRecipientStatus,
        error: str | None = None,
    ) -> None:
        recipient.status = status.value
        recipient.attempted_at = dt.datetime.now(dt.UTC)
        recipient.error = error
        await self.session.flush()

    async def update_status(self, broadcast: Broadcast, status: BroadcastStatus) -> None:
        broadcast.status = status.value
        now = dt.datetime.now(dt.UTC)
        if status == BroadcastStatus.RUNNING and broadcast.started_at is None:
            broadcast.started_at = now
        if status in (BroadcastStatus.COMPLETED, BroadcastStatus.FAILED):
            broadcast.completed_at = now
        if status == BroadcastStatus.CANCELLED:
            broadcast.cancelled_at = now
        await self.session.flush()

    async def increment_counters(
        self, broadcast: Broadcast, *, sent: int = 0, failed: int = 0, skipped: int = 0
    ) -> None:
        broadcast.sent_count += sent
        broadcast.failed_count += failed
        broadcast.skipped_count += skipped
        await self.session.flush()

    async def list_queued_or_running(self) -> list[Broadcast]:
        stmt = select(Broadcast).where(
            Broadcast.status.in_([BroadcastStatus.QUEUED.value, BroadcastStatus.RUNNING.value])
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
