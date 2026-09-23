from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models.plan import PremiumPlan
from app.i18n import t


def promo_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_create_button"), callback_data="promo:create"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_my_codes_button"), callback_data="promo:mine"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_redeem_button"), callback_data="promo:redeem"
                )
            ],
        ]
    )


def promo_kind_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_kind_full"), callback_data="promo_kind:full_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_kind_discount"),
                    callback_data="promo_kind:percent_discount",
                )
            ],
        ]
    )


def promo_plan_keyboard(plans: list[PremiumPlan], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{p.title(language)} — {p.price_amount} {p.currency}",
                callback_data=f"promo_plan:{p.id}",
            )
        ]
        for p in plans
        if p.promo_eligible
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def promo_issuer_keyboard(language: str, *, is_blogger: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "promo_issuer_user"), callback_data="promo_issuer:user"
            )
        ]
    ]
    if is_blogger:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "promo_issuer_blogger"), callback_data="promo_issuer:blogger"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def promo_attribution_choice_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_attribution_yes"), callback_data="promo_attr:yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_attribution_no"), callback_data="promo_attr:no"
                )
            ],
        ]
    )


def promo_confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_confirm_button"), callback_data="promo_confirm:yes"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "menu_cancel"), callback_data="promo_confirm:no"
                )
            ],
        ]
    )
