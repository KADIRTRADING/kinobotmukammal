"""Shared admin-notification helpers used by workers and other handlers.

This module has no message/callback handlers of its own (it's included in
`register_all` for consistency and so `app.bot.handlers` stays the single
place that knows about every router), but centralizes the "send a message
to every admin with a Telegram id and the right role" logic used for:
  - suspicious referral activity (called by the reconciliation worker)
  - payment problems (called by webhook handlers on verification failure)
"""

from __future__ import annotations

from aiogram import Bot, Router

from app.db.models.enums import AdminRole
from app.db.uow import UnitOfWork
from app.i18n import t

router = Router(name="admin_notifications")


async def notify_admins_suspicious_referral(
    bot: Bot, uow: UnitOfWork, *, referrer_label: str, reason: str
) -> None:
    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN]
    )
    text = t("en", "admin_notify_suspicious_referral", referrer=referrer_label, reason=reason)
    for admin in admins:
        try:
            await bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue


async def notify_admins_payment_problem(
    bot: Bot, uow: UnitOfWork, *, order_uid: str, reason: str
) -> None:
    admins = await uow.admins.list_notification_recipients(
        roles=[AdminRole.SUPERADMIN, AdminRole.ADMIN]
    )
    text = t("en", "admin_notify_payment_problem", order_uid=order_uid, reason=reason)
    for admin in admins:
        try:
            await bot.send_message(chat_id=admin.telegram_id, text=text)
        except Exception:
            continue
