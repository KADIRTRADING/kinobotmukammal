"""Admin Categories section: create, edit (title fields), reorder
(up/down), enable, and disable."""

from __future__ import annotations

import html
import re

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_categories import (
    admin_categories_menu_keyboard,
    admin_category_detail_keyboard,
)
from app.bot.keyboards.admin_common import admin_back_row
from app.bot.states import AdminCategoryStates
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t

router = Router(name="admin_categories")

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}[a-z0-9]$")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


@router.callback_query(F.data == "adm:cats")
async def handle_categories_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    categories = await uow.catalog.list_all_categories()
    await callback.message.edit_text(
        t(user.language, "admin_categories_menu_title"),
        reply_markup=admin_categories_menu_keyboard(categories, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ac:view:"))
async def handle_category_view(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    category_id = int(callback.data.split(":")[2])
    category = await uow.catalog.get_category(category_id)
    if category is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    status = "✅" if category.is_active else "⛔"
    await callback.message.edit_text(
        t(
            user.language,
            "admin_category_list_item",
            title=_esc(category.title_uz),
            sort_order=category.sort_order,
            status=status,
        ),
        reply_markup=admin_category_detail_keyboard(category, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ac:toggle:"))
async def handle_category_toggle(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    category_id = int(callback.data.split(":")[2])
    category = await uow.catalog.get_category(category_id)
    if category is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    new_state = not category.is_active
    await uow.catalog.update_category(category, is_active=new_state)
    await record_admin_action(
        uow,
        user,
        action="toggle_category",
        entity_type="category",
        entity_id=str(category_id),
        after={"is_active": new_state},
    )
    key = "admin_category_enabled" if new_state else "admin_category_disabled"
    await callback.answer(t(user.language, key, title=category.title_uz), show_alert=True)
    await handle_category_view(callback, uow, user, **kwargs)


@router.callback_query(F.data.startswith("ac:up:"))
async def handle_category_move_up(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    await _move_category(callback, uow, user, direction="up")


@router.callback_query(F.data.startswith("ac:down:"))
async def handle_category_move_down(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    await _move_category(callback, uow, user, direction="down")


async def _move_category(
    callback: CallbackQuery, uow: UnitOfWork, user: User, *, direction: str
) -> None:
    category_id = int(callback.data.split(":")[2])
    category = await uow.catalog.get_category(category_id)
    if category is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    neighbor = await uow.catalog.get_category_neighbor(category, direction=direction)
    if neighbor is None:
        await callback.answer()
        return
    await uow.catalog.swap_category_sort_order(category, neighbor)
    await record_admin_action(
        uow,
        user,
        action="reorder_category",
        entity_type="category",
        entity_id=str(category_id),
        after={"direction": direction, "swapped_with": neighbor.id},
    )
    await callback.answer(t(user.language, "admin_category_reordered"))
    await handle_category_view(callback, uow, user, **{})


# --- Create category ---------------------------------------------------------------


@router.callback_query(F.data == "ac:add")
async def handle_category_add_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(AdminCategoryStates.awaiting_slug)
    await callback.message.edit_text(
        t(user.language, "admin_category_enter_slug_prompt"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:cats")]
        ),
    )
    await callback.answer()


@router.message(StateFilter(AdminCategoryStates.awaiting_slug), F.text)
async def handle_category_slug_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    slug = message.text.strip().lower()
    if not _SLUG_RE.match(slug):
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    existing = await uow.catalog.get_category_by_slug(slug)
    if existing is not None:
        await message.answer(t(user.language, "admin_category_slug_taken"))
        return
    await state.update_data(slug=slug)
    await state.set_state(AdminCategoryStates.awaiting_title_uz)
    await message.answer(t(user.language, "admin_category_enter_title_uz_prompt"))


@router.message(StateFilter(AdminCategoryStates.awaiting_title_uz), F.text)
async def handle_category_title_uz(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title_uz=message.text.strip())
    await state.set_state(AdminCategoryStates.awaiting_title_ru)
    await message.answer(t(user.language, "admin_category_enter_title_ru_prompt"))


@router.message(StateFilter(AdminCategoryStates.awaiting_title_ru), F.text)
async def handle_category_title_ru(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title_ru=message.text.strip())
    await state.set_state(AdminCategoryStates.awaiting_title_en)
    await message.answer(t(user.language, "admin_category_enter_title_en_prompt"))


@router.message(StateFilter(AdminCategoryStates.awaiting_title_en), F.text)
async def handle_category_title_en(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    category = await uow.catalog.create_category(
        slug=data["slug"],
        title_uz=data["title_uz"],
        title_ru=data["title_ru"],
        title_en=message.text.strip(),
    )
    await record_admin_action(
        uow,
        user,
        action="create_category",
        entity_type="category",
        entity_id=str(category.id),
        after={"slug": category.slug, "title_uz": category.title_uz},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_category_created", title=_esc(category.title_uz)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:cats")]
        ),
    )
