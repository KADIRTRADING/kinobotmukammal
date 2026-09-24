"""aiogram routers for every bot flow, aggregated in `register_all`."""

from __future__ import annotations

from aiogram import Dispatcher

from app.bot.handlers import (
    admin_notifications,
    blogger,
    fallback_text,
    gifts,
    inline_search,
    movies,
    premium,
    promo,
    referrals,
    start,
    support,
    wallet,
)
from app.bot.handlers import (
    settings as settings_handlers,
)
from app.bot.handlers.admin import register_admin_router


def register_all(dp: Dispatcher) -> None:
    """Registration order matters:
    - `start` must be first so `/start` is matched before generic text handlers.
    - The in-Telegram ADMIN PANEL router (`register_admin_router`) is
      registered right after `start` and BEFORE every normal-user feature
      router. It is internally gated end-to-end by
      `app.bot.filters.admin_filter.AdminAccessFilter` (see
      `app.bot.handlers.admin.build_admin_router`), so non-admin updates
      simply fall through to the routers below unaffected -- but admin FSM
      text steps (e.g. "enter the movie code to search") must get first
      refusal ahead of the normal-user movie search / menu-button handlers.
    - `fallback_text` (free-text movie search) MUST be last so every menu
      button / FSM-state text handler in the other routers gets first
      refusal on a text message.
    """
    dp.include_router(start.router)
    register_admin_router(dp)
    dp.include_router(movies.router)
    dp.include_router(inline_search.router)
    dp.include_router(premium.router)
    dp.include_router(wallet.router)
    dp.include_router(referrals.router)
    dp.include_router(blogger.router)
    dp.include_router(promo.router)
    dp.include_router(gifts.router)
    dp.include_router(support.router)
    dp.include_router(settings_handlers.router)
    dp.include_router(admin_notifications.router)
    dp.include_router(fallback_text.router)
