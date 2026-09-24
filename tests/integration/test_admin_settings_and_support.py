"""Integration tests: admin panel "Settings" (safe config toggles + audit
log) and "Support" (ticket list/reply/close) sections, exercised via
`SettingsService`/`SupportRepository`/`AuditLogRepository`, the same
services/repositories `app/bot/handlers/admin/settings.py` and
`app/bot/handlers/admin/support.py` call."""

from __future__ import annotations

import pytest

from app.db.models.enums import SupportSenderType
from app.services.settings_service import SettingsService


@pytest.mark.asyncio
async def test_toggle_referral_commission_on_renewals(uow):
    settings_service = SettingsService(uow)
    assert await settings_service.referral_commission_on_renewals() is False

    await settings_service.set_referral_commission_on_renewals(True)
    assert await settings_service.referral_commission_on_renewals() is True

    await settings_service.set_referral_commission_on_renewals(False)
    assert await settings_service.referral_commission_on_renewals() is False


@pytest.mark.asyncio
async def test_toggle_promo_stacking_allowed(uow):
    settings_service = SettingsService(uow)
    assert await settings_service.promo_stacking_allowed() is False

    await settings_service.set_promo_stacking_allowed(True)
    assert await settings_service.promo_stacking_allowed() is True


@pytest.mark.asyncio
async def test_set_global_blogger_reward_rate_persists_rate_and_currency(uow):
    settings_service = SettingsService(uow)
    await settings_service.set_global_blogger_reward_per_1000(150, "USD")

    rate, currency = await settings_service.global_blogger_reward_per_1000()
    assert rate == 150
    assert currency == "USD"


@pytest.mark.asyncio
async def test_audit_log_records_every_settings_change(uow, make_user):
    from app.bot.handlers.admin.audit_helper import record_admin_action

    admin_actor = await make_user(telegram_id=1234)
    await record_admin_action(
        uow,
        admin_actor,
        action="toggle_setting",
        entity_type="settings",
        entity_id="referral_commission_on_renewals",
        before={"enabled": False},
        after={"enabled": True},
    )

    recent = await uow.audit.list_recent(limit=10)
    assert any(log.entity_type == "settings" for log in recent)


@pytest.mark.asyncio
async def test_support_ticket_list_reply_and_close_flow(uow, make_user):
    user = await make_user()
    ticket = await uow.support.create_ticket(user_id=user.id, subject="Video won't play")

    open_tickets = await uow.support.list_open()
    assert ticket.id in {t.id for t in open_tickets}

    await uow.support.add_message(
        ticket_id=ticket.id,
        sender_type=SupportSenderType.USER,
        sender_id=user.id,
        text="It just spins forever",
    )
    await uow.support.add_message(
        ticket_id=ticket.id,
        sender_type=SupportSenderType.ADMIN,
        sender_id=1234,
        text="Please try again, should be fixed now.",
    )

    thread = await uow.support.list_messages(ticket.id)
    assert len(thread) == 2
    assert thread[0].sender_type == "user"
    assert thread[1].sender_type == "admin"

    await uow.support.close_ticket(ticket)
    closed = await uow.support.get_ticket(ticket.id)
    assert closed.status == "closed"
    assert closed.closed_at is not None

    still_open = await uow.support.list_open()
    assert ticket.id not in {t.id for t in still_open}
