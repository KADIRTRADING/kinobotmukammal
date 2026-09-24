"""Integration tests: admin panel category CRUD + reordering, and
mandatory-channel CRUD (spec sections "Categories" and "Mandatory
channels"), exercised directly against `CatalogRepository` -- the same
repository methods `app/bot/handlers/admin/categories.py` and
`app/bot/handlers/admin/channels.py` call."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_category_auto_assigns_increasing_sort_order(uow):
    cat_a = await uow.catalog.create_category(
        slug="action", title_uz="Jangari", title_ru="Boevik", title_en="Action"
    )
    cat_b = await uow.catalog.create_category(
        slug="comedy", title_uz="Komediya", title_ru="Komediya", title_en="Comedy"
    )
    assert cat_b.sort_order > cat_a.sort_order


@pytest.mark.asyncio
async def test_disabled_category_is_hidden_from_active_list_but_visible_to_admin_list(uow):
    cat = await uow.catalog.create_category(
        slug="drama", title_uz="Drama", title_ru="Drama", title_en="Drama"
    )
    await uow.catalog.update_category(cat, is_active=False)

    active = await uow.catalog.list_active_categories()
    assert cat.id not in {c.id for c in active}

    all_cats = await uow.catalog.list_all_categories()
    assert cat.id in {c.id for c in all_cats}


@pytest.mark.asyncio
async def test_toggle_category_re_enables_it(uow):
    cat = await uow.catalog.create_category(
        slug="horror", title_uz="Horror", title_ru="Horror", title_en="Horror"
    )
    await uow.catalog.update_category(cat, is_active=False)
    await uow.catalog.update_category(cat, is_active=True)

    active = await uow.catalog.list_active_categories()
    assert cat.id in {c.id for c in active}


@pytest.mark.asyncio
async def test_reorder_up_and_down_swaps_sort_order_with_neighbor(uow):
    cat_1 = await uow.catalog.create_category(slug="one", title_uz="1", title_ru="1", title_en="1")
    cat_2 = await uow.catalog.create_category(slug="two", title_uz="2", title_ru="2", title_en="2")
    cat_3 = await uow.catalog.create_category(
        slug="three", title_uz="3", title_ru="3", title_en="3"
    )
    assert cat_1.sort_order < cat_2.sort_order < cat_3.sort_order

    # Move cat_2 "up" (i.e. swap with its immediate lower-sort_order neighbor).
    neighbor = await uow.catalog.get_category_neighbor(cat_2, direction="up")
    assert neighbor.id == cat_1.id
    await uow.catalog.swap_category_sort_order(cat_2, neighbor)

    assert cat_2.sort_order < cat_1.sort_order
    # The very first category in sort order has no "up" neighbor.
    top = await uow.catalog.get_category_neighbor(cat_2, direction="up")
    assert top is None


@pytest.mark.asyncio
async def test_category_slug_must_be_unique_lookup_returns_existing(uow):
    await uow.catalog.create_category(
        slug="scifi", title_uz="Fantastika", title_ru="Fantastika", title_en="Sci-Fi"
    )
    existing = await uow.catalog.get_category_by_slug("scifi")
    assert existing is not None
    assert existing.slug == "scifi"
    missing = await uow.catalog.get_category_by_slug("does-not-exist")
    assert missing is None


@pytest.mark.asyncio
async def test_channel_create_defaults_to_unverified_and_active(uow):
    channel = await uow.catalog.create_channel(
        chat_id="-1001234567890", title="Movie Updates", invite_link="https://t.me/movieupdates"
    )
    assert channel.is_active is True
    assert channel.bot_is_admin_verified is False

    active = await uow.catalog.list_active_channels()
    assert channel.id in {c.id for c in active}


@pytest.mark.asyncio
async def test_channel_verification_flag_is_only_set_after_explicit_update(uow):
    channel = await uow.catalog.create_channel(chat_id="-1009999999999", title="Announcements")
    assert channel.bot_is_admin_verified is False

    # Represents the admin panel's `ah:verify` handler recording a
    # successful LIVE bot.get_chat_member() check -- never faked.
    await uow.catalog.update_channel(channel, bot_is_admin_verified=True)
    refreshed = await uow.catalog.get_channel(channel.id)
    assert refreshed.bot_is_admin_verified is True


@pytest.mark.asyncio
async def test_disabling_a_channel_removes_it_from_active_list(uow):
    channel = await uow.catalog.create_channel(chat_id="-1005555555555", title="Temp")
    await uow.catalog.update_channel(channel, is_active=False)

    active = await uow.catalog.list_active_channels()
    assert channel.id not in {c.id for c in active}

    all_channels = await uow.catalog.list_all_channels()
    assert channel.id in {c.id for c in all_channels}


@pytest.mark.asyncio
async def test_removing_a_channel_hard_deletes_it(uow):
    channel = await uow.catalog.create_channel(chat_id="-1007777777777", title="ToRemove")
    channel_id = channel.id

    await uow.catalog.delete_channel(channel)

    assert await uow.catalog.get_channel(channel_id) is None


@pytest.mark.asyncio
async def test_channel_chat_id_lookup_prevents_duplicate_registration(uow):
    await uow.catalog.create_channel(chat_id="-1001111111111", title="Existing")
    existing = await uow.catalog.get_channel_by_chat_id("-1001111111111")
    assert existing is not None
    # The admin "add channel" FSM checks this before calling create_channel
    # to reject a chat_id that's already registered.
