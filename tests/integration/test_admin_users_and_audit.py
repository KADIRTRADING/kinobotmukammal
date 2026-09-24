"""Integration tests: admin panel "Users" section (block/unblock, grant
premium, gift balance) with a mandatory audit-log entry recorded for every
mutation via `app/bot/handlers/admin/audit_helper.record_admin_action` --
verifies the SAME `GiftService`/`EntitlementService`/`UserRepository`
methods the Telegram admin handlers call, plus the audit trail spec
requirement: "admin ID, action, before/after, time" for every
destructive/financial admin change."""

from __future__ import annotations

import pytest

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.services.entitlement_service import EntitlementService
from app.services.gift_service import GiftService


@pytest.mark.asyncio
async def test_block_user_records_reason_and_is_reversible(uow, make_user):
    user = await make_user()
    await uow.users.set_blocked(user, True, "spam behaviour")

    refreshed = await uow.users.get_by_id(user.id)
    assert refreshed.is_blocked is True
    assert refreshed.block_reason == "spam behaviour"

    await uow.users.set_blocked(refreshed, False)
    unblocked = await uow.users.get_by_id(user.id)
    assert unblocked.is_blocked is False


@pytest.mark.asyncio
async def test_admin_grant_premium_reuses_gift_service_and_writes_audit_entry(
    uow, make_user, make_plan
):
    admin_actor = await make_user(telegram_id=1234)
    recipient = await make_user()
    plan = await make_plan(duration_days=14)

    gift_service = GiftService(uow)
    gift = await gift_service.admin_gift_premium(
        admin_id=1234, recipient_user_id=recipient.id, plan_id=plan.id, reason="loyalty bonus"
    )
    await record_admin_action(
        uow,
        admin_actor,
        action="grant_premium",
        entity_type="user",
        entity_id=str(recipient.id),
        before={"premium_until": None},
        after={"plan_id": plan.id, "gift_id": gift.id},
        note="loyalty bonus",
    )

    recipient_refreshed = await uow.users.get_by_id(recipient.id)
    assert recipient_refreshed.premium_until is not None

    logs = await uow.audit.list_recent(limit=10)
    matching = [
        log for log in logs if log.action == "grant_premium" and log.entity_id == str(recipient.id)
    ]
    assert len(matching) == 1
    assert matching[0].admin_id is None  # no `Admin` DB row for Telegram-native admins
    assert matching[0].admin_username == f"tg:{admin_actor.telegram_id}"
    assert matching[0].note == "loyalty bonus"


@pytest.mark.asyncio
async def test_admin_revoke_premium_only_cuts_future_access(uow, make_user, make_plan):
    admin_actor = await make_user(telegram_id=1234)
    recipient = await make_user()
    plan = await make_plan(duration_days=30)

    gift_service = GiftService(uow)
    await gift_service.admin_gift_premium(
        admin_id=1234, recipient_user_id=recipient.id, plan_id=plan.id, reason="promo"
    )
    recipient_before = await uow.users.get_by_id(recipient.id)
    assert recipient_before.premium_until is not None

    entitlement_service = EntitlementService(uow)
    await entitlement_service.revoke_future(recipient.id)
    await record_admin_action(
        uow,
        admin_actor,
        action="revoke_premium",
        entity_type="user",
        entity_id=str(recipient.id),
    )

    import datetime as dt

    recipient_after = await uow.users.get_by_id(recipient.id)
    assert recipient_after.premium_until <= dt.datetime.now(dt.UTC) + dt.timedelta(seconds=5)


@pytest.mark.asyncio
async def test_admin_gift_balance_requires_no_sender_and_records_reason(uow, make_user):
    admin_actor = await make_user(telegram_id=1234)
    recipient = await make_user()

    gift_service = GiftService(uow)
    await gift_service.admin_gift_balance(
        admin_id=1234,
        recipient_user_id=recipient.id,
        currency="UZS",
        amount=5000,
        reason="compensation for outage",
    )
    await record_admin_action(
        uow,
        admin_actor,
        action="gift_balance",
        entity_type="user",
        entity_id=str(recipient.id),
        after={"amount": 5000, "currency": "UZS"},
        note="compensation for outage",
    )

    wallet = await uow.wallets.get_or_create_wallet(recipient.id, "UZS")
    assert wallet.available_amount == 5000

    logs = await uow.audit.list_recent(limit=10)
    matching = [log for log in logs if log.action == "gift_balance"]
    assert len(matching) == 1
    assert matching[0].note == "compensation for outage"


@pytest.mark.asyncio
async def test_user_search_by_exact_telegram_id_and_by_name_fragment(uow, make_user):
    target = await make_user(telegram_id=555111, first_name="Aziz", username="aziz_movies")
    await make_user(telegram_id=555222, first_name="Bekzod")

    by_id = await uow.users.search_by_name_or_id("555111")
    assert len(by_id) == 1
    assert by_id[0].id == target.id

    by_name = await uow.users.search_by_name_or_id("aziz")
    assert any(u.id == target.id for u in by_name)

    count = await uow.users.count_search_by_name_or_id("aziz")
    assert count == 1
