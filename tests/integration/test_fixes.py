"""Tests for:
1. Exact/full movie code matching (1 does not match 123456789).
2. Group chat filtering: no reply unless mentioned or replied to bot.
3. Mandatory channels: private channels, groups, and join request acceptance.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Chat, Message, User as TgUser

from app.bot.middlewares.group_filter import GroupMentionReplyMiddleware
from app.db.models.catalog import MandatoryChannel
from app.db.models.enums import MovieAccessType, MoviePublicationState
from app.services.movie_access_service import MovieAccessService


async def _make_movie(uow, **kwargs):
    defaults = dict(
        code="123456789",
        title_uz="Test Movie",
        title_ru="Тестовый фильм",
        title_en="Test Movie",
        video_file_id="FAKE_FILE_ID_123",
        access_type=MovieAccessType.FREE.value,
        publication_state=MoviePublicationState.PUBLISHED.value,
    )
    defaults.update(kwargs)
    return await uow.catalog.create(**defaults)


@pytest.mark.asyncio
async def test_movie_code_requires_full_match(uow):
    """If code is 123456789, entering '1' must NOT return the movie."""
    movie = await _make_movie(uow, code="123456789")

    service = MovieAccessService(uow)

    # Searching with partial code '1' must return empty
    res_partial = await service.find_by_code_or_search("1")
    assert res_partial == []

    # Searching with another partial code '123' must return empty
    res_partial2 = await service.find_by_code_or_search("123")
    assert res_partial2 == []

    # Searching with exact full code '123456789' returns the movie
    res_exact = await service.find_by_code_or_search("123456789")
    assert len(res_exact) == 1
    assert res_exact[0].id == movie.id

    # Title search for non-numeric query still works
    res_title = await service.find_by_code_or_search("Test Movie")
    assert len(res_title) == 1
    assert res_title[0].id == movie.id


@pytest.mark.asyncio
async def test_group_mention_reply_middleware():
    """In groups, no reply until someone mentions or replies to the bot."""
    middleware = GroupMentionReplyMiddleware()
    middleware._bot_id = 999
    middleware._bot_username = "testmoviebot"

    handler = AsyncMock(return_value="handled")

    # 1. Private chat message -> always handled
    private_msg = MagicMock(spec=Message)
    private_msg.chat = MagicMock(spec=Chat, type="private")
    res = await middleware(handler, private_msg, {"bot": MagicMock(id=999)})
    assert res == "handled"

    # 2. Group chat message with plain text (no mention, no reply) -> dropped (None)
    group_msg_plain = MagicMock(spec=Message)
    group_msg_plain.chat = MagicMock(spec=Chat, type="supergroup")
    group_msg_plain.reply_to_message = None
    group_msg_plain.entities = []
    group_msg_plain.caption_entities = []
    group_msg_plain.text = "Hello everyone 123456789"
    group_msg_plain.caption = None
    res = await middleware(handler, group_msg_plain, {"bot": MagicMock(id=999)})
    assert res is None  # NOT replied to

    # 3. Group chat message replying to the bot -> handled
    group_msg_reply = MagicMock(spec=Message)
    group_msg_reply.chat = MagicMock(spec=Chat, type="supergroup")
    bot_sender = MagicMock(spec=TgUser, id=999, is_bot=True)
    group_msg_reply.reply_to_message = MagicMock(spec=Message, from_user=bot_sender)
    group_msg_reply.entities = []
    group_msg_reply.caption_entities = []
    group_msg_reply.text = "123456789"
    group_msg_reply.caption = None
    res = await middleware(handler, group_msg_reply, {"bot": MagicMock(id=999)})
    assert res == "handled"

    # 4. Group chat message mentioning the bot -> handled
    group_msg_mention = MagicMock(spec=Message)
    group_msg_mention.chat = MagicMock(spec=Chat, type="group")
    group_msg_mention.reply_to_message = None
    group_msg_mention.entities = []
    group_msg_mention.caption_entities = []
    group_msg_mention.text = "@testmoviebot 123456789"
    group_msg_mention.caption = None
    res = await middleware(handler, group_msg_mention, {"bot": MagicMock(id=999)})
    assert res == "handled"


@pytest.mark.asyncio
async def test_join_request_accepted_as_followed(uow, make_user):
    """If person sent request to join, accept it is like followed."""
    from app.bot.handlers.movies import _get_membership_checker

    user = await make_user()
    movie = await _make_movie(uow, code="999")

    channel = MandatoryChannel(
        chat_id="-100987654321",
        title="Private Join Request Channel",
        invite_link="https://t.me/+joinrequestlink",
        is_active=True,
        bot_is_admin_verified=True,
    )
    uow.session.add(channel)
    await uow.flush()

    bot_mock = MagicMock()
    # Mock bot.get_chat_member to return Left (as Telegram does for pending join requests)
    bot_mock.get_chat_member = AsyncMock(side_effect=Exception("ChatMemberLeft"))

    checker = await _get_membership_checker(bot_mock, uow)
    service = MovieAccessService(uow, membership_checker=checker)

    # Before sending join request: not allowed
    decision_before = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )
    assert decision_before.allowed is False
    assert decision_before.reason == "must_join_channels"

    # User sends join request -> recorded in DB
    await uow.catalog.record_join_request(channel.chat_id, user.telegram_id)
    await uow.flush()

    # After sending join request: accepted as followed!
    decision_after = await service.check_access(
        user_id=user.id, telegram_id=user.telegram_id, movie=movie
    )
    assert decision_after.allowed is True
    assert decision_after.reason == "channels_joined"


@pytest.mark.asyncio
async def test_private_channel_invite_link_ensured(uow):
    """Private channels (-100...) without invite_link get generated links instead of crashing."""
    from app.bot.handlers.movies import ensure_channel_invite_link

    channel = MandatoryChannel(
        chat_id="-1001234567890",
        title="Private Channel",
        invite_link=None,
        is_active=True,
    )
    uow.session.add(channel)
    await uow.flush()

    bot_mock = MagicMock()
    invite_obj = MagicMock()
    invite_obj.invite_link = "https://t.me/+AbCdEfGhIjKlMnOp"
    bot_mock.create_chat_invite_link = AsyncMock(return_value=invite_obj)

    link = await ensure_channel_invite_link(bot_mock, channel, uow)
    assert link == "https://t.me/+AbCdEfGhIjKlMnOp"
    assert channel.invite_link == "https://t.me/+AbCdEfGhIjKlMnOp"


@pytest.mark.asyncio
async def test_group_movie_flow_for_non_bot_user_and_premium(uow):
    """In groups:
    - Non-bot users who send a code receive the 'start the bot to see the movie' message.
    - Premium movies show 'start the bot and buy premium' message."""
    from app.bot.handlers.movies import _present_movie
    from app.i18n import DEFAULT_LANGUAGE, t

    free_movie = await _make_movie(uow, code="222", access_type=MovieAccessType.FREE.value)
    premium_movie = await _make_movie(uow, code="333", access_type=MovieAccessType.PREMIUM.value)

    # 1. Non-bot user (user=None) in supergroup requests free movie 222
    group_msg = MagicMock(spec=Message)
    group_msg.chat = MagicMock(spec=Chat, type="supergroup")
    group_msg.reply = AsyncMock()
    bot_mock = MagicMock()

    await _present_movie(group_msg, uow, user=None, movie=free_movie, bot=bot_mock)
    group_msg.reply.assert_called_once()
    called_text = group_msg.reply.call_args[0][0]
    assert t(DEFAULT_LANGUAGE, "group_movie_not_bot_user") in called_text

    # 2. Non-bot user in supergroup requests premium movie 333
    group_msg2 = MagicMock(spec=Message)
    group_msg2.chat = MagicMock(spec=Chat, type="supergroup")
    group_msg2.reply = AsyncMock()

    await _present_movie(group_msg2, uow, user=None, movie=premium_movie, bot=bot_mock)
    group_msg2.reply.assert_called_once()
    called_text2 = group_msg2.reply.call_args[0][0]
    assert t(DEFAULT_LANGUAGE, "group_movie_premium_required") in called_text2


@pytest.mark.asyncio
async def test_group_watch_callback_gating(uow, make_user):
    """When clicking 'Watch movie' in a group:
    - Non-bot users get alert to start the bot
    - Non-premium users on premium movies get alert to buy premium
    - Authorized bot users have video sent to PM"""
    from aiogram.types import CallbackQuery
    from app.bot.handlers.movies import handle_group_watch
    from app.i18n import DEFAULT_LANGUAGE, t

    free_movie = await _make_movie(uow, code="777", access_type=MovieAccessType.FREE.value)
    prem_movie = await _make_movie(uow, code="888", access_type=MovieAccessType.PREMIUM.value)

    # Case 1: Non-bot user clicks watch on free_movie
    cb_non_bot = MagicMock(spec=CallbackQuery)
    cb_non_bot.data = f"group_watch:{free_movie.id}"
    cb_non_bot.from_user = MagicMock(id=555444333)
    cb_non_bot.answer = AsyncMock()

    await handle_group_watch(cb_non_bot, uow)
    cb_non_bot.answer.assert_called_once()
    assert t(DEFAULT_LANGUAGE, "group_movie_not_bot_user") in cb_non_bot.answer.call_args[0][0]
    assert cb_non_bot.answer.call_args[1].get("show_alert") is True

    # Case 2: Bot user without premium clicks watch on prem_movie
    bot_user = await make_user()
    cb_prem = MagicMock(spec=CallbackQuery)
    cb_prem.data = f"group_watch:{prem_movie.id}"
    cb_prem.from_user = MagicMock(id=bot_user.telegram_id)
    cb_prem.answer = AsyncMock()

    await handle_group_watch(cb_prem, uow)
    cb_prem.answer.assert_called_once()
    assert t(bot_user.language, "group_movie_premium_required") in cb_prem.answer.call_args[0][0]

    # Case 3: Bot user with access clicks watch on free_movie -> delivered to PM
    cb_ok = MagicMock(spec=CallbackQuery)
    cb_ok.data = f"group_watch:{free_movie.id}"
    cb_ok.from_user = MagicMock(id=bot_user.telegram_id)
    cb_ok.answer = AsyncMock()
    cb_ok.bot = MagicMock()
    cb_ok.bot.send_video = AsyncMock()

    await handle_group_watch(cb_ok, uow)
    cb_ok.bot.send_video.assert_called_once()
    assert cb_ok.bot.send_video.call_args[1]["chat_id"] == bot_user.telegram_id
    assert cb_ok.bot.send_video.call_args[1]["video"] == free_movie.video_file_id
    cb_ok.answer.assert_called_once()
    assert t(bot_user.language, "group_movie_sent_to_pm") in cb_ok.answer.call_args[0][0]

