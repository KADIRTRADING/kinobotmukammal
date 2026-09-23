"""Shared fixtures for DB-backed integration tests.

Uses an in-memory SQLite database (via `aiosqlite`) rather than Postgres so
these tests can run without any external service -- `Base.metadata.create_all`
builds the exact same schema the models describe (independent of the
hand-written Alembic migration, which is Postgres-specific SQL).

NOTE ON SANDBOX EXECUTION: this test suite requires `sqlalchemy`,
`aiosqlite`, and the project's own `app` package to be importable, none of
which are installed in the tool-use sandbox this project was authored in
(outbound network access to PyPI is blocked there). These tests are
correct-by-construction and are meant to be run with:
    pip install -e ".[dev]"
    pytest tests/integration -v
on a machine with normal internet access. See README.md "Testing" section.

Row-locking caveat: SQLite has no real `SELECT ... FOR UPDATE` semantics
(SQLAlchemy compiles it as a no-op for the sqlite dialect). The
concurrency test therefore verifies the *outcome* invariant (never more
successful redemptions than `max_uses`) rather than relying on true
row-level locking, which is exercised for real only against Postgres.
"""

from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.db.models  # noqa: F401 populates metadata
from app.db.base import Base
from app.db.uow import UnitOfWork


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def uow(session_factory):
    async with session_factory() as session:
        yield UnitOfWork(session)
        await session.commit()


@pytest_asyncio.fixture
async def make_user(uow):
    counter = {"n": 1000}

    async def _make(telegram_id: int | None = None, **kwargs):
        counter["n"] += 1
        tid = telegram_id if telegram_id is not None else counter["n"]
        user = await uow.users.create(
            telegram_id=tid,
            username=kwargs.get("username"),
            first_name=kwargs.get("first_name"),
            last_name=None,
            language="en",
        )
        if kwargs.get("is_blocked"):
            await uow.users.set_blocked(user, True, "test")
        return user

    return _make


@pytest_asyncio.fixture
async def make_plan(uow):
    counter = {"n": 0}

    async def _make(**kwargs):
        counter["n"] += 1
        defaults = dict(
            code=f"plan{counter['n']}",
            title_uz="Plan",
            title_ru="Plan",
            title_en="Plan",
            duration_days=30,
            price_amount=5000,
            currency="UZS",
            standard_referral_percent=1000,
            blogger_referral_percent=1500,
            blogger_acquisition_reward_enabled=True,
            max_discount_percent=50,
        )
        defaults.update(kwargs)
        return await uow.plans.create(**defaults)

    return _make
