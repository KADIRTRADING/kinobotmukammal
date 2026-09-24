"""Server-side authorization for the in-Telegram admin panel.

This module is the SINGLE source of truth for "is this Telegram user
allowed to perform an admin action right now". It has zero framework
dependencies (no aiogram imports) so its rules can be unit-tested in
isolation; `app.bot.filters.admin_filter.AdminAccessFilter` is the thin
aiogram adapter that calls into it.

Security model (spec requirements):
  - There are TWO tiers of admin identity, both still nothing more than a
    numeric Telegram id -- neither has a username/password:
      1. "Owners" -- `Settings.telegram_superadmin_ids`, read fresh from
         config on every check. Changing the env var and restarting the
         process is enough to add/remove an owner; no code change, no DB
         row needed. Owners are the ONLY identities allowed to grant or
         revoke tier-2 access (see `is_owner_admin` below and
         `app.bot.handlers.admin.admins`) -- this one-directional trust
         means a compromised or careless granted admin can never
         privilege-escalate by adding more admins of their own.
      2. "Granted admins" -- rows in the `admin_grants` DB table
         (`app.db.models.admin_grant.AdminGrant`, `is_active=True`),
         created by an owner from inside the in-Telegram admin panel's
         "👑 Admins" section. This is what lets an owner add a
         co-administrator at runtime with NO `.env` edit and NO restart.
    Both tiers pass the exact same `is_authorized_admin` check below and
    get full access to every other admin-panel section (movies, users,
    orders, etc.) -- the only thing gated by tier is the Admins section's
    mutating actions themselves.
  - Authorization is decided ENTIRELY from the numeric Telegram user id of
    the actual sender of the current update, as reported by Telegram
    itself (`Message.from_user.id` / `CallbackQuery.from_user.id`). A
    user-supplied id (e.g. typed into a message, or a forwarded message's
    original-sender id) is NEVER accepted as proof of identity -- see
    `AdminContext.is_forwarded` below, which forces rejection.
  - Every admin-only handler is wrapped by `AdminAccessFilter`, which is
    evaluated by aiogram BEFORE the handler body runs, for EVERY message,
    callback query, and FSM state transition that touches admin state.
    Hiding the "🛠 Admin panel" button from non-admins (see
    app.bot.keyboards.common.main_menu_keyboard) is a pure UX nicety and
    is never treated as an authorization boundary by itself.
  - Admin actions are rejected when:
      * the sender's numeric id is not in the allowlist,
      * the update did not happen in a private chat (groups/channels are
        never a valid admin surface, even for an allowlisted id -- this
        also prevents someone screen-sharing a group chat from acting as
        admin, and prevents accidental admin commands in a support group),
      * the incoming message is a forwarded message (a forwarded message's
        buttons/callback data cannot be trusted as originating from the
        forwarder's own tap, and its "original sender" must never be
        confused with the actual current sender).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SuperadminIdsSource(Protocol):
    """Structural type for whatever settings object is passed in.

    Deliberately a `Protocol`, not a hard import of `app.config.Settings`,
    so this module has NO dependency on pydantic/pydantic-settings and can
    be imported and unit-tested in any plain Python 3 environment. Any
    object exposing a `telegram_superadmin_ids` collection of ints
    satisfies this (the real `app.config.Settings` does).
    """

    telegram_superadmin_ids: frozenset[int]


@dataclass(frozen=True)
class AdminAccessContext:
    """Everything needed to decide authorization, extracted from the raw
    Telegram update by the aiogram-level filter. Kept as a plain dataclass
    (no aiogram types) so `is_authorized_admin` stays framework-free and
    trivially unit-testable.
    """

    telegram_user_id: int | None
    """The numeric Telegram id of whoever actually sent/tapped this update,
    as reported by Telegram -- never a value read from message text."""

    chat_type: str | None
    """Telegram chat type string: 'private', 'group', 'supergroup', 'channel'."""

    is_forwarded: bool = False
    """True if the underlying Message has `forward_origin` set (Bot API
    7.0+) i.e. it was forwarded rather than typed/tapped directly by the
    sender in this chat."""


@dataclass(frozen=True)
class AdminAccessDecision:
    allowed: bool
    reason: str


def is_authorized_admin(
    context: AdminAccessContext,
    settings: SuperadminIdsSource,
    granted_admin_ids: frozenset[int] = frozenset(),
) -> AdminAccessDecision:
    """Pure authorization check. Called by the aiogram filter AND directly
    inside handler bodies for defense-in-depth (see module docstring).

    `granted_admin_ids` is the current set of ACTIVE `AdminGrant.telegram_id`
    rows (tier 2). Passing the default empty set makes this function behave
    exactly as before for any caller that hasn't been updated yet -- e.g.
    existing unit tests that only exercise the env allowlist.
    """
    if context.telegram_user_id is None:
        return AdminAccessDecision(False, "no_sender_identity")

    if (
        context.telegram_user_id not in settings.telegram_superadmin_ids
        and context.telegram_user_id not in granted_admin_ids
    ):
        return AdminAccessDecision(False, "not_in_allowlist")

    if context.is_forwarded:
        return AdminAccessDecision(False, "forwarded_message_rejected")

    if context.chat_type is not None and context.chat_type != "private":
        return AdminAccessDecision(False, "not_private_chat")

    return AdminAccessDecision(True, "authorized")


def is_superadmin_id(
    telegram_user_id: int | None,
    settings: SuperadminIdsSource,
    granted_admin_ids: frozenset[int] = frozenset(),
) -> bool:
    """Cheap boolean check used for UI decisions only (e.g. whether to show
    the "🛠 Admin panel" button, for owners AND granted admins alike). NEVER
    use this alone to gate an action -- always go through
    `is_authorized_admin` at the point the action executes, so chat-type
    and forwarded-message checks are also applied.
    """
    if telegram_user_id is None:
        return False
    return (
        telegram_user_id in settings.telegram_superadmin_ids
        or telegram_user_id in granted_admin_ids
    )


def is_owner_admin(telegram_user_id: int | None, settings: SuperadminIdsSource) -> bool:
    """True only for a tier-1 "owner" (an id listed in the
    `TELEGRAM_SUPERADMIN_IDS` env var), never for a tier-2 granted admin.
    This is the ONLY check that should gate the Admins section's
    grant/revoke actions -- a granted admin must never be able to grant or
    revoke access for anyone, including themselves, which would otherwise
    let a single compromised granted-admin account permanently entrench
    itself or add more admins.
    """
    return telegram_user_id is not None and telegram_user_id in settings.telegram_superadmin_ids
