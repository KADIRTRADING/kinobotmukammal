"""Broadcast queueing. Actual message delivery (rate-limited, resumable) is
performed by `app.workers.broadcast_worker`, never inline in a request
handler, so admin actions never block on sending thousands of messages.
"""

from __future__ import annotations

from app.db.models.broadcast import Broadcast
from app.db.models.enums import BroadcastStatus, BroadcastTarget
from app.db.uow import UnitOfWork


class BroadcastService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def create_draft(
        self,
        *,
        admin_id: int,
        target: BroadcastTarget,
        text_uz: str,
        text_ru: str,
        text_en: str,
        photo_file_id: str | None = None,
        button_text: str | None = None,
        button_url: str | None = None,
        target_language: str | None = None,
        custom_user_ids: list[int] | None = None,
        rate_limit_per_second: int = 20,
    ) -> Broadcast:
        return await self.uow.broadcasts.create(
            created_by_admin_id=admin_id,
            target=target.value,
            target_language=target_language,
            custom_user_ids=custom_user_ids,
            text_uz=text_uz,
            text_ru=text_ru,
            text_en=text_en,
            photo_file_id=photo_file_id,
            button_text=button_text,
            button_url=button_url,
            rate_limit_per_second=rate_limit_per_second,
            status=BroadcastStatus.DRAFT.value,
        )

    async def enqueue(self, broadcast: Broadcast) -> int:
        """Resolve the recipient list NOW (snapshotting membership so the
        run is reproducible/auditable) and mark the broadcast QUEUED for the
        worker to pick up."""
        target = BroadcastTarget(broadcast.target)
        if target == BroadcastTarget.CUSTOM_IDS:
            user_ids = broadcast.custom_user_ids or []
        elif target == BroadcastTarget.ALL:
            users = await self.uow.users.iter_broadcast_targets()
            user_ids = [u.id for u in users]
        elif target == BroadcastTarget.PREMIUM:
            users = await self.uow.users.iter_broadcast_targets(premium_only=True)
            user_ids = [u.id for u in users]
        elif target == BroadcastTarget.FREE:
            users = await self.uow.users.iter_broadcast_targets(premium_only=False)
            user_ids = [u.id for u in users]
        elif target == BroadcastTarget.LANGUAGE:
            users = await self.uow.users.iter_broadcast_targets(language=broadcast.target_language)
            user_ids = [u.id for u in users]
        else:
            user_ids = []

        await self.uow.broadcasts.add_recipients(broadcast.id, user_ids)
        broadcast.total_recipients = len(user_ids)
        await self.uow.broadcasts.update_status(broadcast, BroadcastStatus.QUEUED)
        return len(user_ids)

    async def cancel(self, broadcast: Broadcast) -> None:
        await self.uow.broadcasts.update_status(broadcast, BroadcastStatus.CANCELLED)
