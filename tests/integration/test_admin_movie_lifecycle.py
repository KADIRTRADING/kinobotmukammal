"""Integration tests: admin movie catalog lifecycle (spec sections on the
in-Telegram admin panel's "Movies" section) -- draft creation, publish,
archive, hard delete, and admin-scoped search across every publication
state via `CatalogRepository` (reused directly by
`app/bot/handlers/admin/movies.py`, no duplicated business logic)."""

from __future__ import annotations

import pytest

from app.db.models.enums import MovieAccessType, MoviePublicationState


async def _make_movie(uow, **overrides):
    defaults = dict(
        code="mv001",
        title_uz="Sarlavha",
        title_ru="Titre",
        title_en="Title",
        video_file_id="BAACAgIAAxkBAAtest",
        access_type=MovieAccessType.FREE.value,
        publication_state=MoviePublicationState.DRAFT.value,
    )
    defaults.update(overrides)
    return await uow.catalog.create(**defaults)


@pytest.mark.asyncio
async def test_movie_is_created_as_draft_and_not_publicly_searchable(uow):
    movie = await _make_movie(uow, code="mv100")
    assert movie.publication_state == MoviePublicationState.DRAFT.value

    # Draft never appears in the end-user-facing published search...
    public_hits = await uow.catalog.search_published("mv100")
    assert public_hits == []

    # ...but IS visible to the admin panel's any-state search (spec:
    # admins must be able to find a draft they haven't published yet).
    admin_hits = await uow.catalog.search_any_state("mv100")
    assert len(admin_hits) == 1
    assert admin_hits[0].id == movie.id


@pytest.mark.asyncio
async def test_publish_makes_movie_visible_to_public_search(uow):
    movie = await _make_movie(uow, code="mv101")
    await uow.catalog.update(movie, publication_state=MoviePublicationState.PUBLISHED.value)

    public_hits = await uow.catalog.search_published("mv101")
    assert len(public_hits) == 1
    assert public_hits[0].id == movie.id


@pytest.mark.asyncio
async def test_archive_removes_movie_from_public_search_but_keeps_the_row(uow):
    movie = await _make_movie(uow, code="mv102")
    await uow.catalog.update(movie, publication_state=MoviePublicationState.PUBLISHED.value)
    assert len(await uow.catalog.search_published("mv102")) == 1

    await uow.catalog.update(movie, publication_state=MoviePublicationState.ARCHIVED.value)

    assert await uow.catalog.search_published("mv102") == []
    # Still resolvable by id / admin any-state search -- archiving is
    # non-destructive by design (see CatalogRepository.delete docstring).
    still_there = await uow.catalog.get_by_id(movie.id)
    assert still_there is not None
    assert still_there.publication_state == MoviePublicationState.ARCHIVED.value


@pytest.mark.asyncio
async def test_delete_hard_removes_the_movie_row(uow):
    movie = await _make_movie(uow, code="mv103")
    movie_id = movie.id

    await uow.catalog.delete(movie)

    assert await uow.catalog.get_by_id(movie_id) is None
    assert await uow.catalog.search_any_state("mv103") == []


@pytest.mark.asyncio
async def test_list_all_movies_includes_every_publication_state(uow):
    await _make_movie(uow, code="mv200", publication_state=MoviePublicationState.DRAFT.value)
    await _make_movie(uow, code="mv201", publication_state=MoviePublicationState.PUBLISHED.value)
    await _make_movie(uow, code="mv202", publication_state=MoviePublicationState.ARCHIVED.value)

    all_movies = await uow.catalog.list_all_movies()
    codes = {m.code for m in all_movies}
    assert {"mv200", "mv201", "mv202"} <= codes

    total = await uow.catalog.count_movies()
    assert total >= 3


@pytest.mark.asyncio
async def test_movie_code_must_be_unique_for_admin_upload_flow(uow):
    await _make_movie(uow, code="dup001")
    # The admin FSM checks `get_by_code` before ever calling `create` to
    # reject a duplicate code at the input step -- verify that check works.
    existing = await uow.catalog.get_by_code("dup001")
    assert existing is not None
