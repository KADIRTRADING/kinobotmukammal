"""Keyboards for the admin Promo Codes section. Callback namespace: `apr:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row, admin_pagination_row
from app.db.models.plan import PremiumPlan
from app.db.models.promo import PromoCode
from app.i18n import t


def admin_promos_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_promos_pending_button"), callback_data="apr:pending:0"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_promos_create_button"), callback_data="apr:create"
            )
        ],
        admin_back_row(language, "adm:root"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_promo_pending_list_keyboard(
    promos: list[PromoCode], language: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=p.code, callback_data=f"apr:view:{p.id}")] for p in promos]
    nav = admin_pagination_row(language, prefix="apr:pending:", page=page, total_pages=total_pages)
    if nav:
        rows.append(nav)
    rows.append(admin_back_row(language, "adm:promos"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_promo_review_keyboard(promo_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_promo_approve_button"),
                    callback_data=f"apr:approve:{promo_id}",
                ),
                InlineKeyboardButton(
                    text=t(language, "admin_promo_reject_button"),
                    callback_data=f"apr:reject:{promo_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_promo_cancel_button"),
                    callback_data=f"apr:cancel:{promo_id}",
                )
            ],
            admin_back_row(language, "adm:promos"),
        ]
    )


def admin_promo_plan_pick_keyboard(plans: list[PremiumPlan], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{p.code} — {p.price_amount} {p.currency}",
                callback_data=f"apr:createplan:{p.id}",
            )
        ]
        for p in plans
        if p.promo_eligible
    ]
    rows.append(admin_back_row(language, "adm:promos"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_promo_kind_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "promo_kind_full"), callback_data="apr:createkind:full_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "promo_kind_discount"),
                    callback_data="apr:createkind:percent_discount",
                )
            ],
        ]
    )
