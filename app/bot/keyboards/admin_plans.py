"""Keyboards for the admin Premium Plans section. Callback namespace: `ap:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row
from app.db.models.plan import PremiumPlan
from app.i18n import t


def admin_plans_menu_keyboard(plans: list[PremiumPlan], language: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(language, "admin_plan_add_button"), callback_data="ap:add")]
    ]
    for p in plans:
        status = "✅" if p.is_active else "⛔"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {p.code} — {p.price_amount} {p.currency}",
                    callback_data=f"ap:view:{p.id}",
                )
            ]
        )
    rows.append(admin_back_row(language, "adm:root"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_plan_detail_keyboard(plan: PremiumPlan, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_plan_edit_price_button"),
                    callback_data=f"ap:editprice:{plan.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_plan_edit_standard_referral_button"),
                    callback_data=f"ap:editstd:{plan.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_plan_edit_blogger_referral_button"),
                    callback_data=f"ap:editblg:{plan.id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_plan_toggle_button"),
                    callback_data=f"ap:toggle:{plan.id}",
                )
            ],
            admin_back_row(language, "adm:plans"),
        ]
    )
