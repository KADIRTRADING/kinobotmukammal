"""Keyboards for the admin Orders/Payments section. Callback namespace: `ao:`."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row, admin_pagination_row
from app.db.models.order import Order
from app.i18n import t


def admin_orders_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_orders_recent_button"), callback_data="ao:list:0"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_orders_filter_status_button"), callback_data="ao:filter"
            )
        ],
        admin_back_row(language, "adm:root"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_orders_status_filter_keyboard(language: str) -> InlineKeyboardMarkup:
    statuses = ["pending", "paid", "failed", "cancelled", "refunded", "disputed"]
    rows = [[InlineKeyboardButton(text=s, callback_data=f"ao:list_status:{s}:0")] for s in statuses]
    rows.append(admin_back_row(language, "adm:orders"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_order_list_keyboard(
    orders: list[Order], language: str, page: int, total_pages: int, *, prefix: str
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{str(o.uid)[:8]} {o.status}", callback_data=f"ao:view:{o.id}")]
        for o in orders
    ]
    nav = admin_pagination_row(language, prefix=prefix, page=page, total_pages=total_pages)
    if nav:
        rows.append(nav)
    rows.append(admin_back_row(language, "adm:orders"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_order_detail_keyboard(order: Order, language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(language, "admin_order_provider_events_button"),
                callback_data=f"ao:events:{order.id}",
            )
        ],
    ]
    if order.status == "paid":
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "admin_order_refund_button"),
                    callback_data=f"ao:refund:{order.id}",
                )
            ]
        )
    rows.append(admin_back_row(language, "adm:orders"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_order_refund_confirm_keyboard(order_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_confirm_button"),
                    callback_data=f"ao:refund_confirm:{order_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_cancel_button"), callback_data=f"ao:view:{order_id}"
                )
            ],
        ]
    )
