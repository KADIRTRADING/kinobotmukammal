"""In-Telegram admin panel: every handler in this package is registered on
`admin_router`, which is gated end-to-end by
`app.bot.filters.admin_filter.AdminAccessFilter` (see `register_admin_router`
below). No handler in this package should ever be reachable by a sender
who is not on `Settings.telegram_superadmin_ids`, sending from a private
chat, with a non-forwarded message -- that invariant is enforced once,
here, rather than repeated in every individual handler.

Sub-modules (one per admin panel section, matching the spec):
    dashboard.py    -- statistics overview
    movies.py       -- movie CRUD (upload/draft/preview/publish/edit/archive/delete/search)
    categories.py   -- category CRUD + reordering
    channels.py     -- mandatory channel CRUD + bot-admin verification
    users.py        -- user search/status/history/block/premium/gift
    plans.py        -- premium plan CRUD
    promos.py       -- promo code review/create/moderate
    bloggers.py     -- blogger applications + suspicious referral review
    support.py      -- support ticket list/reply/close
    broadcasts.py   -- broadcast compose/preview/confirm/progress
    orders.py       -- order/payment browsing + manual refund (never fake-paid)
    settings.py     -- global settings + audit log viewer
    root.py         -- the "🛠 Admin panel" entry point and top-level menu
"""

from __future__ import annotations

from aiogram import Dispatcher, Router

from app.bot.filters.admin_filter import AdminAccessFilter
from app.bot.handlers.admin import (
    bloggers,
    broadcasts,
    categories,
    channels,
    dashboard,
    movies,
    orders,
    plans,
    promos,
    root,
    support,
    users,
)
from app.bot.handlers.admin import (
    settings as settings_module,
)


def build_admin_router() -> Router:
    """Aggregates every admin sub-router under one parent router and
    attaches `AdminAccessFilter` to that PARENT's message/callback-query
    observers. In aiogram 3, a filter attached via `router.message.filter()`
    / `router.callback_query.filter()` is evaluated for every update that
    reaches this router, INCLUDING updates destined for its included
    sub-routers -- so every handler defined in every sub-module below is
    transparently covered without each of them repeating the filter.
    """
    admin_router = Router(name="admin_panel")
    admin_router.message.filter(AdminAccessFilter())
    admin_router.callback_query.filter(AdminAccessFilter())

    admin_router.include_router(root.router)
    admin_router.include_router(dashboard.router)
    admin_router.include_router(movies.router)
    admin_router.include_router(categories.router)
    admin_router.include_router(channels.router)
    admin_router.include_router(users.router)
    admin_router.include_router(plans.router)
    admin_router.include_router(promos.router)
    admin_router.include_router(bloggers.router)
    admin_router.include_router(support.router)
    admin_router.include_router(broadcasts.router)
    admin_router.include_router(orders.router)
    admin_router.include_router(settings_module.router)

    return admin_router


def register_admin_router(dp: Dispatcher) -> None:
    """Called from `app.bot.handlers.register_all`. Must be included
    BEFORE `fallback_text.router` (the free-text movie-search catch-all)
    so admin FSM text steps (e.g. "enter the movie code") are consumed by
    the admin panel and never misinterpreted as a movie search query --
    and BEFORE the normal per-feature routers' menu-button handlers so an
    admin's tap on "🛠 Admin panel" (which is plain message text) cannot be
    shadowed by an identically-labelled normal-user button (it never is,
    since the label is unique, but registering first is the same
    first-match-wins guarantee aiogram already documents).
    """
    dp.include_router(build_admin_router())
