"""Integration tests: free access, premium access, mandatory-subscription
exemption for premium users, and that access is denied when membership
can't be verified (fail closed) (spec section 10)."""

from __future__ import annotations

import datetime as dt

import pytest

from app.db.models.enums import MovieAccessType, MoviePublicationState
from app.services.movie_access_service import MovieAccessService


async def _make_movie(uow, **kwargs):
    defaults = dict(
        code="100",
        title_uz="T",
        title_ru="T",
        title_en="T",
        video_file_id="FAKE_FILE_ID",
        access_type=MovieAccessType.FREE.value,
        publication_state=MoviePublicationState.PUBLISHED.value,
    )
    defaults.update(kwargs)
    return await uow.catalog.create(**defaults)


@pytest.mark.asyncio
async def test_free_movie_without_mandatory_channels_is_accessible(uow, make_user):
    user = await make_user()
    movie = await _make_movie(uow, code="1")

    service = MovieAccessService(uow)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is True
    assert decision.reason == "no_mandatory_channels"


@pytest.mark.asyncio
async def test_premium_movie_requires_active_premium(uow, make_user):
    user = await make_user()
    movie = await _make_movie(uow, code="2", access_type=MovieAccessType.PREMIUM.value)

    service = MovieAccessService(uow)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )
    assert decision.allowed is False
    assert decision.reason == "premium_required"

    user.premium_until = dt.datetime.now(dt.UTC) + dt.timedelta(days=1)
    await uow.flush()
    decision2 = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )
    assert decision2.allowed is True
    assert decision2.reason == "premium_access"


@pytest.mark.asyncio
async def test_premium_user_is_exempt_from_mandatory_subscription(uow, make_user):
    user = await make_user()
    user.premium_until = dt.datetime.now(dt.UTC) + dt.timedelta(days=1)
    await uow.flush()

    from app.db.models.catalog import MandatoryChannel

    channel = MandatoryChannel(chat_id="@somechannel", title="Some Channel")
    uow.session.add(channel)
    await uow.flush()

    movie = await _make_movie(uow, code="3", access_type=MovieAccessType.FREE.value)

    async def checker(telegram_id, chat_id):
        return False  # not a member of anything

    service = MovieAccessService(uow, membership_checker=checker)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is True
    assert decision.reason == "premium_exempt"


@pytest.mark.asyncio
async def test_free_user_must_join_mandatory_channels(uow, make_user):
    user = await make_user()

    from app.db.models.catalog import MandatoryChannel

    channel = MandatoryChannel(chat_id="@somechannel", title="Some Channel")
    uow.session.add(channel)
    await uow.flush()

    movie = await _make_movie(uow, code="4")

    async def not_a_member(telegram_id, chat_id):
        return False

    service = MovieAccessService(uow, membership_checker=not_a_member)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is False
    assert decision.reason == "must_join_channels"
    assert "@somechannel" in decision.missing_channels


@pytest.mark.asyncio
async def test_access_fails_closed_when_membership_cannot_be_checked(uow, make_user):
    user = await make_user()

    from app.db.models.catalog import MandatoryChannel

    channel = MandatoryChannel(chat_id="@somechannel", title="Some Channel")
    uow.session.add(channel)
    await uow.flush()

    movie = await _make_movie(uow, code="5")

    service = MovieAccessService(uow, membership_checker=None)  # no live Telegram connection
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is False
    assert decision.reason == "membership_check_unavailable"


@pytest.mark.asyncio
async def test_unpublished_movie_is_never_accessible(uow, make_user):
    user = await make_user()
    movie = await _make_movie(uow, code="6", publication_state=MoviePublicationState.DRAFT.value)

    service = MovieAccessService(uow)
    decision = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )

    assert decision.allowed is False
    assert decision.reason == "not_published"
