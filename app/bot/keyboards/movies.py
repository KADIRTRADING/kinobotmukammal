from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models.catalog import Category, MandatoryChannel, Movie
from app.i18n import t


def category_list_keyboard(categories: list[Category], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=c.title(language) if hasattr(c, "title") else _cat_title(c, language),
                callback_data=f"cat:{c.id}",
            )
        ]
        for c in categories
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _cat_title(category: Category, language: str) -> str:
    return {"uz": category.title_uz, "ru": category.title_ru, "en": category.title_en}.get(
        language, category.title_uz
    )


def movie_search_results_keyboard(movies: list[Movie], language: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{m.title(language)} ({m.code})", callback_data=f"movie:{m.id}"
            )
        ]
        for m in movies
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def join_channels_keyboard(
    channels: list[MandatoryChannel], movie_id: int, language: str
) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        url = ch.invite_link or f"https://t.me/{ch.chat_id.lstrip('@')}"
        rows.append([InlineKeyboardButton(text=ch.title, url=url)])
    rows.append(
        [
            InlineKeyboardButton(
                text=t(language, "movie_check_membership_button"),
                callback_data=f"check_membership:{movie_id}",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def open_in_bot_keyboard(bot_username: str, movie_code: str, language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(language, "movie_open_in_bot_button"),
                    url=f"https://t.me/{bot_username}?start=movie_{movie_code}",
                )
            ]
        ]
    )
