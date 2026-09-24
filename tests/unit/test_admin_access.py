"""Unit tests for the pure admin-authorization logic in
`app.core.admin_access`. No aiogram/pydantic/DB dependency -- these run in
any plain Python 3 environment, exactly like the module under test.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.admin_access import (
    AdminAccessContext,
    is_authorized_admin,
    is_owner_admin,
    is_superadmin_id,
)


@dataclass(frozen=True)
class _FakeSettings:
    """Minimal stand-in for `app.config.Settings` satisfying the
    `SuperadminIdsSource` protocol, so these tests don't need pydantic
    installed to exercise the pure authorization logic."""

    telegram_superadmin_ids: frozenset[int]


def _settings(ids: str = "1234") -> _FakeSettings:
    parsed: set[int] = set()
    for raw in ids.split(","):
        raw = raw.strip()
        if not raw:
            continue
        try:
            parsed.add(int(raw))
        except ValueError:
            continue
    return _FakeSettings(telegram_superadmin_ids=frozenset(parsed))


def test_allowlisted_id_in_private_chat_is_authorized():
    ctx = AdminAccessContext(telegram_user_id=1234, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"))
    assert decision.allowed is True
    assert decision.reason == "authorized"


def test_non_allowlisted_id_is_rejected():
    ctx = AdminAccessContext(telegram_user_id=9999, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"))
    assert decision.allowed is False
    assert decision.reason == "not_in_allowlist"


def test_allowlisted_id_in_group_chat_is_rejected():
    ctx = AdminAccessContext(telegram_user_id=1234, chat_type="group", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"))
    assert decision.allowed is False
    assert decision.reason == "not_private_chat"


def test_allowlisted_id_in_supergroup_is_rejected():
    ctx = AdminAccessContext(telegram_user_id=1234, chat_type="supergroup", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"))
    assert decision.allowed is False
    assert decision.reason == "not_private_chat"


def test_forwarded_message_from_allowlisted_id_is_rejected():
    ctx = AdminAccessContext(telegram_user_id=1234, chat_type="private", is_forwarded=True)
    decision = is_authorized_admin(ctx, _settings("1234"))
    assert decision.allowed is False
    assert decision.reason == "forwarded_message_rejected"


def test_missing_sender_identity_is_rejected():
    ctx = AdminAccessContext(telegram_user_id=None, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"))
    assert decision.allowed is False
    assert decision.reason == "no_sender_identity"


def test_empty_allowlist_rejects_everyone():
    ctx = AdminAccessContext(telegram_user_id=1234, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings(""))
    assert decision.allowed is False
    assert decision.reason == "not_in_allowlist"


def test_multiple_ids_in_allowlist():
    settings = _settings("1234,5678, 999")
    assert settings.telegram_superadmin_ids == frozenset({1234, 5678, 999})

    ctx_a = AdminAccessContext(telegram_user_id=5678, chat_type="private", is_forwarded=False)
    ctx_b = AdminAccessContext(telegram_user_id=1, chat_type="private", is_forwarded=False)
    assert is_authorized_admin(ctx_a, settings).allowed is True
    assert is_authorized_admin(ctx_b, settings).allowed is False


def test_real_settings_parses_allowlist_identically_to_fake(monkeypatch):
    """Cross-checks that `app.config.Settings.telegram_superadmin_ids`
    (the real implementation used in production) parses the same way as
    the `_FakeSettings` test double above, so these unit tests stay a
    faithful proxy for the real authorization path. Skipped automatically
    if pydantic isn't installed in the current environment (see
    tests/unit -- this whole module otherwise avoids that dependency)."""
    pytest = __import__("pytest")
    try:
        from app.config import Settings
    except ModuleNotFoundError:
        pytest.skip("pydantic not installed in this environment")

    real = Settings(TELEGRAM_SUPERADMIN_IDS="1234, not-a-number, 5678")
    fake = _settings("1234, not-a-number, 5678")
    assert real.telegram_superadmin_ids == fake.telegram_superadmin_ids


def test_malformed_allowlist_entries_are_ignored_not_fatal():
    settings = _settings("1234, not-a-number, 5678")
    assert settings.telegram_superadmin_ids == frozenset({1234, 5678})


def test_user_supplied_id_never_grants_access_by_itself():
    """Simulates someone typing '1234' as message text hoping to be
    treated as that admin: the authorization decision only ever looks at
    `telegram_user_id`, which the filter populates strictly from
    `event.from_user.id` (server-verified by Telegram), never from message
    text. This test documents that a context whose `telegram_user_id` is
    the *actual* sender (e.g. 9999, who merely typed the string "1234")
    is rejected regardless of what text they sent.
    """
    ctx = AdminAccessContext(telegram_user_id=9999, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"))
    assert decision.allowed is False


def test_is_superadmin_id_helper_matches_full_check_for_private_direct_messages():
    settings = _settings("1234")
    assert is_superadmin_id(1234, settings) is True
    assert is_superadmin_id(9999, settings) is False
    assert is_superadmin_id(None, settings) is False


# --- Tier-2 "granted admin" tests (runtime admin_grants, see app.core.admin_access
# module docstring for the two-tier owner/granted model) ------------------------


def test_granted_admin_id_in_private_chat_is_authorized_even_though_not_an_owner():
    ctx = AdminAccessContext(telegram_user_id=5555, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"), granted_admin_ids=frozenset({5555}))
    assert decision.allowed is True
    assert decision.reason == "authorized"


def test_granted_admin_id_still_rejected_in_group_chat():
    ctx = AdminAccessContext(telegram_user_id=5555, chat_type="group", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"), granted_admin_ids=frozenset({5555}))
    assert decision.allowed is False
    assert decision.reason == "not_private_chat"


def test_granted_admin_id_still_rejected_when_forwarded():
    ctx = AdminAccessContext(telegram_user_id=5555, chat_type="private", is_forwarded=True)
    decision = is_authorized_admin(ctx, _settings("1234"), granted_admin_ids=frozenset({5555}))
    assert decision.allowed is False
    assert decision.reason == "forwarded_message_rejected"


def test_id_not_in_either_owner_or_granted_set_is_rejected():
    ctx = AdminAccessContext(telegram_user_id=9999, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"), granted_admin_ids=frozenset({5555}))
    assert decision.allowed is False
    assert decision.reason == "not_in_allowlist"


def test_default_empty_granted_set_behaves_identically_to_pre_grant_feature_behavior():
    """Backward-compat guard: any caller that doesn't pass `granted_admin_ids`
    (e.g. old test code, or a caller yet to be updated) must see the exact
    same behavior as before this tier was introduced."""
    ctx = AdminAccessContext(telegram_user_id=1234, chat_type="private", is_forwarded=False)
    decision = is_authorized_admin(ctx, _settings("1234"))
    assert decision.allowed is True


def test_is_superadmin_id_helper_also_recognizes_granted_admins():
    settings = _settings("1234")
    assert is_superadmin_id(5555, settings, granted_admin_ids=frozenset({5555})) is True
    assert is_superadmin_id(5555, settings) is False  # not granted without the set
    assert is_superadmin_id(1234, settings, granted_admin_ids=frozenset()) is True  # owner


def test_is_owner_admin_is_true_only_for_env_listed_ids_never_for_granted_admins():
    settings = _settings("1234")
    assert is_owner_admin(1234, settings) is True
    assert is_owner_admin(5555, settings) is False  # granted-admin id, not an owner
    assert is_owner_admin(None, settings) is False


def test_granted_admin_cannot_be_mistaken_for_owner_even_if_ids_look_similar():
    """Documents that owner-only actions (grant/revoke) must gate on
    `is_owner_admin`, never on `is_authorized_admin`/`is_superadmin_id` --
    a granted admin passes both of the latter but must fail the former."""
    settings = _settings("1234")
    granted = frozenset({5555})
    assert (
        is_authorized_admin(
            AdminAccessContext(telegram_user_id=5555, chat_type="private"), settings, granted
        ).allowed
        is True
    )
    assert is_superadmin_id(5555, settings, granted) is True
    assert is_owner_admin(5555, settings) is False
