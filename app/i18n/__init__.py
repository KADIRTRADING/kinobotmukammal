"""Lightweight i18n: no external i18n framework dependency, just nested
dict lookups with a safe fallback chain (requested language -> Uzbek ->
key itself), so a missing translation never crashes a handler.
"""

from __future__ import annotations

from app.i18n.en import TRANSLATIONS as EN
from app.i18n.ru import TRANSLATIONS as RU
from app.i18n.uz import TRANSLATIONS as UZ

_CATALOGS = {"uz": UZ, "ru": RU, "en": EN}
DEFAULT_LANGUAGE = "uz"
SUPPORTED_LANGUAGES = ("uz", "ru", "en")


def t(language: str, key: str, **kwargs) -> str:
    catalog = _CATALOGS.get(language, _CATALOGS[DEFAULT_LANGUAGE])
    template = catalog.get(key)
    if template is None:
        template = _CATALOGS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        return template
