"""Keyboards for the admin Movies section.

Callback namespace: `am:` (admin movies). All ids embedded in callback
data are plain decimal integers (`Movie.id`), keeping every string well
under Telegram's 64-byte `callback_data` limit.
"""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.bot.keyboards.admin_common import admin_back_row, admin_pagination_row
from app.db.models.catalog import Category, Movie
from app.i18n import t


def admin_movies_menu_keyboard(language: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(language, "admin_movies_add_button"), callback_data="am:add")],
        [
            InlineKeyboardButton(
                text=t(language, "admin_movies_list_button"), callback_data="am:list:0"
            )
        ],
        [
            InlineKeyboardButton(
                text=t(language, "admin_movies_search_button"), callback_data="am:search"
            )
        ],
        admin_back_row(language),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_movie_list_keyboard(
    movies: list[Movie], language: str, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{m.code} | {m.title(language)[:30]}", callback_data=f"am:view:{m.id}"
            )
        ]
        for m in movies
    ]
    nav = admin_pagination_row(language, prefix="am:list:", page=page, total_pages=total_pages)
    if nav:
        rows.append(nav)
    rows.append(admin_back_row(language, "adm:movies"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_category_pick_keyboard(
    categories: list[Category], language: str, *, callback_prefix: str
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=c.title_uz, callback_data=f"{callback_prefix}{c.id}")]
        for c in categories
    ]
    rows.append(
        [
            InlineKeyboardButton(
                text=t(language, "admin_movie_no_category_button"),
                callback_data=f"{callback_prefix}0",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_access_type_keyboard(language: str, *, callback_prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_access_free_button"),
                    callback_data=f"{callback_prefix}free",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_access_premium_button"),
                    callback_data=f"{callback_prefix}premium",
                )
            ],
        ]
    )


def admin_movie_draft_confirm_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_confirm_button"), callback_data="am:draft_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_cancel_button"), callback_data="am:draft_cancel"
                )
            ],
        ]
    )


def admin_movie_detail_keyboard(movie: Movie, language: str) -> InlineKeyboardMarkup:
    rows = []
    if movie.publication_state != "published":
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_publish_button"),
                    callback_data=f"am:publish:{movie.id}",
                )
            ]
        )
    if movie.publication_state != "archived":
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_archive_button"),
                    callback_data=f"am:archive:{movie.id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(language, "admin_movie_edit_button"), callback_data=f"am:edit:{movie.id}"
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(language, "admin_movie_replace_video_button"),
                callback_data=f"am:replvid:{movie.id}",
            ),
            InlineKeyboardButton(
                text=t(language, "admin_movie_replace_poster_button"),
                callback_data=f"am:replpost:{movie.id}",
            ),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(language, "admin_movie_delete_button"), callback_data=f"am:del:{movie.id}"
            )
        ]
    )
    rows.append(admin_back_row(language, "adm:movies"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_movie_delete_confirm_keyboard(movie_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_confirm_button"),
                    callback_data=f"am:del_confirm:{movie_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_cancel_button"), callback_data=f"am:view:{movie_id}"
                )
            ],
        ]
    )


def admin_movie_edit_field_keyboard(movie_id: int, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_edit_title_uz_button"),
                    callback_data=f"am:editf:{movie_id}:title_uz",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_edit_title_ru_button"),
                    callback_data=f"am:editf:{movie_id}:title_ru",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_edit_title_en_button"),
                    callback_data=f"am:editf:{movie_id}:title_en",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_edit_category_button"),
                    callback_data=f"am:editf:{movie_id}:category",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(language, "admin_movie_edit_access_button"),
                    callback_data=f"am:editf:{movie_id}:access",
                )
            ],
            admin_back_row(language, f"am:view:{movie_id}"),
        ]
    )
