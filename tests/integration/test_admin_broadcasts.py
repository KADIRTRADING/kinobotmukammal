"""Integration tests: admin panel "Broadcasts" section -- create draft,
enqueue (which snapshots the recipient list and marks QUEUED for the
worker to pick up -- NEVER sends inline from the admin handler), dedupe
via the unique `(broadcast_id, user_id)` constraint, and cancel, all via
`BroadcastService`, the same service `app/bot/handlers/admin/broadcasts.py`
calls."""

from __future__ import annotations

import pytest

from app.db.models.enums import BroadcastStatus, BroadcastTarget
from app.services.broadcast_service import BroadcastService


@pytest.mark.asyncio
async def test_create_draft_starts_in_draft_status_with_no_recipients_yet(uow):
    broadcast_service = BroadcastService(uow)
    broadcast = await broadcast_service.create_draft(
        admin_id=1234,
        target=BroadcastTarget.ALL,
        text_uz="Salom!",
        text_ru="Privet!",
        text_en="Hello!",
    )
    assert broadcast.status == BroadcastStatus.DRAFT.value
    assert broadcast.total_recipients == 0


@pytest.mark.asyncio
async def test_enqueue_all_target_snapshots_every_non_blocked_user(uow, make_user):
    await make_user()
    await make_user()
    blocked = await make_user()
    await uow.users.set_blocked(blocked, True, "spam")

    broadcast_service = BroadcastService(uow)
    broadcast = await broadcast_service.create_draft(
        admin_id=1234,
        target=BroadcastTarget.ALL,
        text_uz="Salom!",
        text_ru="Privet!",
        text_en="Hello!",
    )
    recipient_count = await broadcast_service.enqueue(broadcast)

    # Blocked users are excluded (see UserRepository.iter_broadcast_targets).
    assert recipient_count == 2
    refreshed = await uow.broadcasts.get(broadcast.id)
    assert refreshed.status == BroadcastStatus.QUEUED.value
    assert refreshed.total_recipients == 2


@pytest.mark.asyncio
async def test_enqueue_premium_target_only_includes_active_premium_users(uow, make_user, make_plan):
    premium_user = await make_user()
    free_user = await make_user()
    plan = await make_plan(duration_days=30)

    from app.db.models.enums import EntitlementSource
    from app.services.entitlement_service import EntitlementService

    await EntitlementService(uow).grant(
        user_id=premium_user.id,
        plan_id=plan.id,
        duration_days=30,
        source=EntitlementSource.ADMIN_GRANT,
        source_reference="test-grant",
    )

    broadcast_service = BroadcastService(uow)
    broadcast = await broadcast_service.create_draft(
        admin_id=1234,
        target=BroadcastTarget.PREMIUM,
        text_uz="Premium xabari",
        text_ru="Premium",
        text_en="Premium message",
    )
    recipient_count = await broadcast_service.enqueue(broadcast)

    assert recipient_count == 1
    recipients = await uow.broadcasts.list_pending_recipients(broadcast.id)
    assert {r.user_id for r in recipients} == {premium_user.id}
    assert free_user.id not in {r.user_id for r in recipients}


@pytest.mark.asyncio
async def test_enqueue_snapshot_is_deduplicated_by_unique_constraint(uow, make_user):
    user = await make_user()
    broadcast_service = BroadcastService(uow)
    broadcast = await broadcast_service.create_draft(
        admin_id=1234,
        target=BroadcastTarget.CUSTOM_IDS,
        text_uz="x",
        text_ru="x",
        text_en="x",
        custom_user_ids=[user.id],
    )
    await broadcast_service.enqueue(broadcast)

    recipients = await uow.broadcasts.list_pending_recipients(broadcast.id)
    assert len(recipients) == 1

    # Adding the exact same recipient again must violate the unique
    # constraint (broadcast_id, user_id) -- this is the DB-level guarantee
    # the worker's resumable per-recipient tracking relies on to prevent a
    # duplicate send if the worker restarts mid-run.
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        await uow.broadcasts.add_recipients(broadcast.id, [user.id])
    await uow.session.rollback()


@pytest.mark.asyncio
async def test_cancel_queued_broadcast_sets_cancelled_status(uow, make_user):
    await make_user()
    broadcast_service = BroadcastService(uow)
    broadcast = await broadcast_service.create_draft(
        admin_id=1234,
        target=BroadcastTarget.ALL,
        text_uz="x",
        text_ru="x",
        text_en="x",
    )
    await broadcast_service.enqueue(broadcast)

    await broadcast_service.cancel(broadcast)

    refreshed = await uow.broadcasts.get(broadcast.id)
    assert refreshed.status == BroadcastStatus.CANCELLED.value
    assert refreshed.cancelled_at is not None
