from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models.plan import PremiumPlan
from app.i18n import t


def plan_list_keyboard(plans: list[PremiumPlan], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(
                    language,
                    "premium_plan_button",
                    title=plan.title(language),
                    price=plan.price_amount,
                    currency=plan.currency,
                ),
                callback_data=f"plan:{plan.id}",
            )
        ]
        for plan in plans
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_method_keyboard(
    language: str, plan_id: int, *, stars_enabled: bool, wallet_enabled: bool
) -> InlineKeyboardMarkup:
    rows = []
    if stars_enabled:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "premium_pay_with_stars"), callback_data=f"pay:stars:{plan_id}"
                )
            ]
        )
    if wallet_enabled:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "premium_pay_with_wallet"),
                    callback_data=f"pay:wallet:{plan_id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text=t(language, "menu_cancel"), callback_data="nav:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def skip_promo_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "premium_skip_promo"), callback_data="promo:skip"
                )
            ]
        ]
    )
