"""Integration tests: admin panel "Blogger applications & referrals"
section -- approve/reject an application with a reason, suspend/reactivate
an active blogger, and list suspicious referrals for review, all via
`BloggerService`/`ReferralRepository`, the same services
`app/bot/handlers/admin/bloggers.py` calls."""

from __future__ import annotations

import pytest

from app.services.blogger_service import BloggerService


@pytest.mark.asyncio
async def test_approve_application_activates_blogger_profile(uow, make_user):
    applicant = await make_user()
    blogger_service = BloggerService(uow)
    start = await blogger_service.start_application(applicant_user_id=applicant.id)
    assert start.already_pending is False

    await blogger_service.decide(
        start.application, approve=True, admin_id=1234, reason="verified bio link"
    )

    profile = await uow.bloggers.get_profile_by_user(applicant.id)
    assert profile is not None
    assert profile.status == "active"

    refreshed_applicant = await uow.users.get_by_id(applicant.id)
    assert refreshed_applicant.blogger_status_cache == "approved"


@pytest.mark.asyncio
async def test_reject_application_requires_reason_and_leaves_no_profile(uow, make_user):
    applicant = await make_user()
    blogger_service = BloggerService(uow)
    start = await blogger_service.start_application(applicant_user_id=applicant.id)

    await blogger_service.decide(
        start.application, approve=False, admin_id=1234, reason="bio link does not match applicant"
    )

    profile = await uow.bloggers.get_profile_by_user(applicant.id)
    assert profile is None

    refreshed_applicant = await uow.users.get_by_id(applicant.id)
    assert refreshed_applicant.blogger_status_cache == "rejected"

    application = await uow.bloggers.get_application(start.application.id)
    assert application.decision_reason == "bio link does not match applicant"


@pytest.mark.asyncio
async def test_suspend_and_reactivate_active_blogger(uow, make_user):
    applicant = await make_user()
    blogger_service = BloggerService(uow)
    start = await blogger_service.start_application(applicant_user_id=applicant.id)
    await blogger_service.decide(start.application, approve=True, admin_id=1234)

    suspended_ok = await blogger_service.suspend(applicant.id, reason="policy violation")
    assert suspended_ok is True
    profile = await uow.bloggers.get_profile_by_user(applicant.id)
    assert profile.status == "suspended"
    refreshed = await uow.users.get_by_id(applicant.id)
    assert refreshed.blogger_status_cache == "suspended"

    reactivated_ok = await blogger_service.reactivate(applicant.id)
    assert reactivated_ok is True
    profile_after = await uow.bloggers.get_profile_by_user(applicant.id)
    assert profile_after.status == "active"


@pytest.mark.asyncio
async def test_suspend_a_user_with_no_blogger_profile_returns_false(uow, make_user):
    non_blogger = await make_user()
    blogger_service = BloggerService(uow)
    result = await blogger_service.suspend(non_blogger.id, reason="n/a")
    assert result is False


@pytest.mark.asyncio
async def test_pending_applications_queue_lists_only_pending(uow, make_user):
    blogger_service = BloggerService(uow)
    applicant_a = await make_user()
    applicant_b = await make_user()

    start_a = await blogger_service.start_application(applicant_user_id=applicant_a.id)
    await blogger_service.start_application(applicant_user_id=applicant_b.id)
    await blogger_service.decide(start_a.application, approve=True, admin_id=1234)

    pending = await uow.bloggers.list_pending()
    pending_applicant_ids = {p.applicant_user_id for p in pending}
    assert applicant_a.id not in pending_applicant_ids
    assert applicant_b.id in pending_applicant_ids


@pytest.mark.asyncio
async def test_suspicious_referrals_are_listed_separately_for_admin_review(uow, make_user):
    referrer = await make_user()
    referred = await make_user()
    await uow.referrals.create(
        referred_user_id=referred.id,
        referrer_user_id=referrer.id,
        is_suspicious=True,
        suspicious_reason="same device fingerprint as referrer",
    )

    suspicious = await uow.referrals.list_suspicious()
    assert any(r.referred_user_id == referred.id for r in suspicious)

    count = await uow.referrals.count_suspicious()
    assert count >= 1


@pytest.mark.asyncio
async def test_starting_a_second_application_while_pending_returns_the_existing_one(uow, make_user):
    applicant = await make_user()
    blogger_service = BloggerService(uow)
    first = await blogger_service.start_application(applicant_user_id=applicant.id)
    second = await blogger_service.start_application(applicant_user_id=applicant.id)

    assert first.already_pending is False
    assert second.already_pending is True
    assert second.application.id == first.application.id
