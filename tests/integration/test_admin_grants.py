"""Integration tests: runtime-manageable admin grants (the "👑 Admins"
section) -- an owner granting/revoking admin-panel access to another
Telegram id at runtime, via `AdminManagementService`/`AdminGrantRepository`,
the same objects `app/bot/handlers/admin/admins.py` calls.

These tests exercise the DB-persistence half of the two-tier owner/granted
model; the pure authorization-decision half (owner vs. granted vs.
neither) is covered by `tests/unit/test_admin_access.py`.
"""

from __future__ import annotations

import pytest

from app.services.admin_management_service import AdminManagementService


@pytest.mark.asyncio
async def test_granting_a_new_telegram_id_creates_an_active_row(uow):
    service = AdminManagementService(uow)
    grant = await service.grant(telegram_id=555111, granted_by_telegram_id=1234, label="@new_admin")

    assert grant.telegram_id == 555111
    assert grant.is_active is True
    assert grant.granted_by_telegram_id == 1234
    assert grant.label == "@new_admin"

    active_ids = await uow.admin_grants.list_active_telegram_ids()
    assert 555111 in active_ids


@pytest.mark.asyncio
async def test_revoking_a_grant_deactivates_it_but_keeps_the_history_row(uow):
    service = AdminManagementService(uow)
    await service.grant(telegram_id=555222, granted_by_telegram_id=1234, label="temp")

    revoked = await service.revoke(555222, revoked_by_telegram_id=1234)
    assert revoked is not None
    assert revoked.is_active is False
    assert revoked.revoked_by_telegram_id == 1234
    assert revoked.revoked_at is not None

    active_ids = await uow.admin_grants.list_active_telegram_ids()
    assert 555222 not in active_ids

    # History is preserved -- list_all still returns the revoked row.
    all_grants = await service.list_grants(active_only=False)
    assert any(g.telegram_id == 555222 for g in all_grants)


@pytest.mark.asyncio
async def test_revoking_a_never_granted_id_is_a_safe_no_op(uow):
    service = AdminManagementService(uow)
    result = await service.revoke(999999, revoked_by_telegram_id=1234)
    assert result is None


@pytest.mark.asyncio
async def test_revoking_an_already_revoked_grant_is_a_safe_no_op(uow):
    service = AdminManagementService(uow)
    await service.grant(telegram_id=555333, granted_by_telegram_id=1234)
    await service.revoke(555333, revoked_by_telegram_id=1234)

    second_attempt = await service.revoke(555333, revoked_by_telegram_id=1234)
    assert second_attempt is None


@pytest.mark.asyncio
async def test_re_granting_after_revocation_reactivates_the_same_row_not_a_duplicate(uow):
    service = AdminManagementService(uow)
    first = await service.grant(telegram_id=555444, granted_by_telegram_id=1234, label="v1")
    first_id = first.id
    await service.revoke(555444, revoked_by_telegram_id=1234)

    second = await service.grant(telegram_id=555444, granted_by_telegram_id=1234, label="v2")
    assert second.id == first_id  # same row, reactivated -- never a duplicate
    assert second.is_active is True
    assert second.label == "v2"
    assert second.revoked_by_telegram_id is None
    assert second.revoked_at is None


@pytest.mark.asyncio
async def test_owner_cannot_grant_admin_access_to_themselves(uow):
    service = AdminManagementService(uow)
    with pytest.raises(ValueError):
        await service.grant(telegram_id=1234, granted_by_telegram_id=1234)


@pytest.mark.asyncio
async def test_list_active_excludes_revoked_grants_list_all_includes_them(uow):
    service = AdminManagementService(uow)
    await service.grant(telegram_id=555555, granted_by_telegram_id=1234, label="stays active")
    await service.grant(telegram_id=555666, granted_by_telegram_id=1234, label="gets revoked")
    await service.revoke(555666, revoked_by_telegram_id=1234)

    active = await service.list_grants(active_only=True)
    active_ids = {g.telegram_id for g in active}
    assert 555555 in active_ids
    assert 555666 not in active_ids

    everyone = await service.list_grants(active_only=False)
    everyone_ids = {g.telegram_id for g in everyone}
    assert 555555 in everyone_ids
    assert 555666 in everyone_ids


@pytest.mark.asyncio
async def test_granted_admin_becomes_authorized_end_to_end_via_the_filter_data_path(uow):
    """Verifies the exact data `AdminAccessFilter` reads
    (`uow.admin_grants.list_active_telegram_ids()`) reflects a grant made
    through the service layer -- i.e. the full path an owner's "Add admin"
    action feeds into the authorization check on the NEXT message from the
    newly granted id, with no restart or cache to invalidate."""
    from app.core.admin_access import AdminAccessContext, is_authorized_admin

    class _FakeSettings:
        telegram_superadmin_ids = frozenset({1234})

    service = AdminManagementService(uow)
    await service.grant(telegram_id=777777, granted_by_telegram_id=1234, label="new admin")

    granted_ids = await uow.admin_grants.list_active_telegram_ids()
    ctx = AdminAccessContext(telegram_user_id=777777, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _FakeSettings(), granted_ids)
    assert decision.allowed is True
