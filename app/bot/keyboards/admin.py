from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from app.db.models.catalog import Category, MandatoryChannel


def admin_main_inline_keyboard(
    web_app_url: str | None = None, browser_url: str | None = None
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🎬 Kino qo'shish", callback_data="admin:movie:add"),
            InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="admin:movie:delete"),
        ],
        [
            InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats"),
            InlineKeyboardButton(text="📢 Kanallar", callback_data="admin:channels"),
        ],
        [
            InlineKeyboardButton(text="✉️ Xabar yuborish", callback_data="admin:broadcast"),
            InlineKeyboardButton(text="🎟 Promo kod", callback_data="admin:promo"),
        ],
    ]
    if web_app_url:
        web_row = [
            InlineKeyboardButton(
                text="📱 Web Panel (Mini App)", web_app=WebAppInfo(url=web_app_url)
            )
        ]
        if browser_url:
            web_row.append(InlineKeyboardButton(text="🌐 Brauzerda ochish", url=browser_url))
        rows.append(web_row)
    rows.append([InlineKeyboardButton(text="❌ Yopish", callback_data="admin:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_cancel_inline_keyboard(callback_data: str = "admin:cancel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data=callback_data)]]
    )


def admin_confirm_inline_keyboard(
    yes_cb: str, no_cb: str = "admin:cancel"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=yes_cb),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data=no_cb),
            ]
        ]
    )


def admin_categories_inline_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    buttons = []
    # 2 columns of categories
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(text=cat.title_uz, callback_data=f"admin:cat:{cat.id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append(
        [InlineKeyboardButton(text="🚫 Kategoriyasiz", callback_data="admin:cat:none")]
    )
    buttons.append(
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_access_type_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Bepul (FREE)", callback_data="admin:access:free"),
                InlineKeyboardButton(
                    text="⭐ Faqat Premium (PREMIUM)", callback_data="admin:access:premium"
                ),
            ],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:cancel")],
        ]
    )


def admin_channels_inline_keyboard(
    channels: list[MandatoryChannel],
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="admin:channel:add"),
            InlineKeyboardButton(text="🔄 Huquqlarni tekshirish", callback_data="admin:channel:check"),
        ]
    ]
    for ch in channels:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"🗑 {ch.title[:20]} ni o'chirish",
                    callback_data=f"admin:channel:del:{ch.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_promo_type_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ 100% Bepul Premium", callback_data="admin:promo:type:full_premium"
                ),
                InlineKeyboardButton(
                    text="🏷 Chegirma (%)", callback_data="admin:promo:type:discount"
                ),
            ],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:cancel")],
        ]
    )
