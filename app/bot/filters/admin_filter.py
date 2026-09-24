"""aiogram adapter around `app.core.admin_access`.

`AdminAccessFilter` is attached to every admin router (via
`router.message.filter(...)` / `router.callback_query.filter(...)`) so
aiogram itself refuses to dispatch to ANY admin handler for a sender that
isn't authorized -- the check runs before the handler body, for every
message, callback query, and (because FSM state handlers are ordinary
message/callback handlers in aiogram) every state transition.

This is intentionally a thin, dumb adapter: all the actual authorization
rules live in `app.core.admin_access.is_authorized_admin`, which has no
aiogram dependency and is unit-tested directly.
"""

from __future__ import annotations

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from app.config import Settings, get_settings
from app.core.admin_access import AdminAccessContext, is_authorized_admin
from app.db.uow import UnitOfWork


class AdminAccessFilter(BaseFilter):
    """Returns True only for messages/callbacks from an allowlisted
    Telegram id (env owner OR an active DB `AdminGrant`), sent directly
    (not forwarded) in a private chat.

    Rejected updates are silently filtered out by aiogram (the router
    simply doesn't match), so an unauthorized sender gets no response at
    all from admin-only handlers -- exactly as if the handlers didn't
    exist. This is deliberate: it avoids confirming to a prober whether a
    given callback_data string is "valid but unauthorized" versus
    "unrecognized".

    aiogram calls filters with the same keyword-argument data dict it
    passes to handlers (see `Dispatcher`/`Router` dependency injection),
    so `uow` is available here exactly like it is inside a handler body --
    `DbSessionMiddleware` runs before this filter is ever evaluated (it is
    an `outer_middleware`, filters run inside the update-processing chain
    it wraps). No extra plumbing is required.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings

    async def __call__(self, event: Message | CallbackQuery, uow: UnitOfWork, **kwargs) -> bool:
        settings = self._settings or get_settings()
        context = _build_context(event)
        granted_admin_ids = await uow.admin_grants.list_active_telegram_ids()
        decision = is_authorized_admin(context, settings, granted_admin_ids)
        return decision.allowed


def _build_context(event: Message | CallbackQuery) -> AdminAccessContext:
    if isinstance(event, CallbackQuery):
        message = event.message
        chat_type = message.chat.type if message is not None else None
        # Callback queries themselves cannot be "forwarded" -- only the
        # message carrying the inline keyboard could have been, and a
        # forwarded message's inline keyboard is never actionable by
        # Telegram in the first place. We still surface the underlying
        # message's forwarded flag defensively.
        is_forwarded = _is_forwarded(message) if message is not None else False
        return AdminAccessContext(
            telegram_user_id=event.from_user.id if event.from_user else None,
            chat_type=chat_type,
            is_forwarded=is_forwarded,
        )

    if isinstance(event, Message):
        return AdminAccessContext(
            telegram_user_id=event.from_user.id if event.from_user else None,
            chat_type=event.chat.type if event.chat else None,
            is_forwarded=_is_forwarded(event),
        )

    return AdminAccessContext(telegram_user_id=None, chat_type=None, is_forwarded=False)


def _is_forwarded(message: Message) -> bool:
    """True if this message was forwarded rather than typed/tapped
    directly by its sender. Checks the modern `forward_origin` field
    (Bot API 7.0+) and falls back to the legacy `forward_date`/
    `forward_from` fields for defense-in-depth across aiogram versions.
    """
    if getattr(message, "forward_origin", None) is not None:
        return True
    if getattr(message, "forward_date", None) is not None:
        return True
    if getattr(message, "forward_from", None) is not None:
        return True
    if getattr(message, "forward_from_chat", None) is not None:
        return True
    return False
