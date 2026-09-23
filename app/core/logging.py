"""Structured JSON logging setup.

Deliberately never logs: bot tokens, payment provider secrets, webhook
signatures, or Telegram `file_id` values for protected videos (a leaked
`video_file_id` would let anyone fetch the licensed content directly from
Telegram, bypassing entitlement checks). Call `redact()` before logging any
dict that might contain such fields.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

_SENSITIVE_KEYS = {
    "bot_token",
    "token",
    "password",
    "password_hash",
    "secret",
    "api_key",
    "webhook_secret",
    "video_file_id",
    "stripe_api_key",
    "click_secret_key",
    "authorization",
}


def redact(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if k.lower() in _SENSITIVE_KEYS:
            out[k] = "***redacted***"
        elif isinstance(v, dict):
            out[k] = redact(v)
        else:
            out[k] = v
    return out


class _SafeFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        return msg


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(
        _SafeFormatter(
            fmt='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":%(message)r}'
        )
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Silence noisy third-party libraries at DEBUG.
    for noisy in ("httpx", "aiogram.event"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
