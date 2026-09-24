"""Locks in the i18n contract: uz/ru/en must always expose the exact same
translation keys, and each key's `{placeholder}` set must match across all
three languages so `t(lang, key, **kwargs)` never raises for one language
while working for another.
"""

from __future__ import annotations

import re

from app.i18n.en import TRANSLATIONS as EN
from app.i18n.ru import TRANSLATIONS as RU
from app.i18n.uz import TRANSLATIONS as UZ

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def _placeholders(template: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(template))


def test_all_three_languages_expose_the_same_key_set():
    uz, ru, en = set(UZ), set(RU), set(EN)
    assert uz == ru, f"uz/ru key mismatch: {uz ^ ru}"
    assert uz == en, f"uz/en key mismatch: {uz ^ en}"


def test_every_key_has_matching_placeholders_across_languages():
    mismatches = []
    for key in UZ:
        p_uz = _placeholders(UZ[key])
        p_ru = _placeholders(RU[key])
        p_en = _placeholders(EN[key])
        if not (p_uz == p_ru == p_en):
            mismatches.append((key, p_uz, p_ru, p_en))
    assert not mismatches, f"Placeholder mismatches: {mismatches}"


def test_admin_panel_keys_are_present():
    """Spot-checks that the admin-panel key namespace introduced for the
    in-Telegram admin panel actually exists (regression guard)."""
    required_prefixes = (
        "admin_menu_button",
        "admin_dashboard_",
        "admin_movies_",
        "admin_movie_",
        "admin_categories_",
        "admin_category_",
        "admin_channels_",
        "admin_channel_",
        "admin_users_",
        "admin_user_",
        "admin_plans_",
        "admin_plan_",
        "admin_promos_",
        "admin_promo_",
        "admin_bloggers_",
        "admin_blogger_",
        "admin_support_",
        "admin_broadcasts_",
        "admin_broadcast_",
        "admin_orders_",
        "admin_order_",
        "admin_settings_",
        "admin_audit_",
    )
    for prefix in required_prefixes:
        assert any(k.startswith(prefix) for k in UZ), f"No key found with prefix {prefix!r}"
