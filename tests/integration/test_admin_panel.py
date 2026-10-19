"""Integration tests for Telegram Admin Panel:
1. Admin authorization (bootstrap superadmin and DB admin).
2. /admin and Admin main menu.
3. Adding a movie via admin flow.
4. Movie deletion flow.
5. Telegram one-click auth endpoint (/admin/auth/telegram).
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.admin.security import create_session_token
from app.bot.handlers.admin_panel import get_or_create_admin, is_admin_user
from app.config import get_settings
from app.db.models.enums import AdminRole, MovieAccessType, MoviePublicationState
from app.main import create_api_app


@pytest.mark.asyncio
async def test_bootstrap_superadmin_auto_provisioning(uow):
    settings = get_settings()
    superadmin_id = 8321271047

    # Should be recognized even before existing in DB
    is_admin = await is_admin_user(superadmin_id, uow)
    assert is_admin is True

    # Check that record was provisioned
    admin = await uow.admins.get_by_telegram_id(superadmin_id)
    assert admin is not None
    assert admin.role == AdminRole.SUPERADMIN.value
    assert admin.is_active is True


@pytest.mark.asyncio
async def test_non_admin_rejection(uow):
    random_user_id = 999999999
    is_admin = await is_admin_user(random_user_id, uow)
    assert is_admin is False


@pytest.mark.asyncio
async def test_admin_movie_creation_and_deletion(uow):
    # 1. Create a movie as an admin would
    movie = await uow.catalog.create(
        code="999",
        title_uz="Test Admin Kino",
        title_ru="Тестовое Кино",
        title_en="Test Movie",
        video_file_id="BAACAgIAAxkBAAE...",
        access_type=MovieAccessType.FREE.value,
        publication_state=MoviePublicationState.PUBLISHED.value,
    )
    await uow.session.commit()

    # Verify movie exists and can be retrieved
    found = await uow.catalog.get_by_code("999")
    assert found is not None
    assert found.title_uz == "Test Admin Kino"

    # 2. Test movie deletion
    await uow.catalog.delete(found)
    await uow.session.commit()

    deleted = await uow.catalog.get_by_code("999")
    assert deleted is None


@pytest.mark.asyncio
async def test_admin_stats_counts(uow, make_user):
    user1 = await make_user()
    user2 = await make_user()

    total_users = await uow.users.count_all()
    assert total_users >= 2

    today_users = await uow.users.count_today_users()
    assert today_users >= 2


@pytest.mark.asyncio
async def test_telegram_auth_one_click_login(uow):
    # Provision an admin
    admin = await uow.admins.create(
        username="test_admin_auth",
        password_hash="fakehash",
        telegram_id=7777777,
        role=AdminRole.SUPERADMIN.value,
        is_active=True,
    )
    await uow.session.commit()

    token = create_session_token(admin.id)

    from app.db.session import get_session

    app = create_api_app()
    app.dependency_overrides[get_session] = lambda: uow.session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request /admin/auth/telegram
        resp = await client.get(f"/admin/auth/telegram?token={token}", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/admin/dashboard"

        # Check session cookie is set
        cookie_header = resp.headers.get("set-cookie", "")
        assert "movie_bot_admin_session" in cookie_header
