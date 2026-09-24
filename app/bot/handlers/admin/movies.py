"""Admin Movies section: upload a video, collect metadata, save as draft,
preview, publish, edit metadata, replace video/poster, archive, delete
(with confirmation), and search by code.

Every mutation reuses `UnitOfWork.catalog` (the same `CatalogRepository`
the public-facing movie browsing handlers read from), so there is exactly
one code path that creates/edits a `Movie` row -- no parallel business
logic is duplicated here.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.keyboards.admin_common import admin_back_row, paginate
from app.bot.keyboards.admin_movies import (
    admin_access_type_keyboard,
    admin_category_pick_keyboard,
    admin_movie_delete_confirm_keyboard,
    admin_movie_detail_keyboard,
    admin_movie_draft_confirm_keyboard,
    admin_movie_edit_field_keyboard,
    admin_movie_list_keyboard,
    admin_movies_menu_keyboard,
)
from app.bot.states import MovieAdminStates
from app.db.models.enums import MoviePublicationState
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t

router = Router(name="admin_movies")


def _esc(text: str | None) -> str:
    """Escapes user-provided text for safe inclusion in an HTML-parse-mode
    Telegram message (the bot's default parse mode -- see
    app.bot.factory.build_bot). Every piece of admin- or catalog-authored
    free text rendered back to the admin goes through this."""
    return html.escape(text or "")


# --- Menu -----------------------------------------------------------------------


@router.callback_query(F.data == "adm:movies")
async def handle_movies_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_movies_menu_title"),
        reply_markup=admin_movies_menu_keyboard(user.language),
    )
    await callback.answer()


# --- List -------------------------------------------------------------------------


@router.callback_query(F.data.startswith("am:list:"))
async def handle_movies_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    page = int(callback.data.split(":")[2])
    all_movies = await uow.catalog.list_all_movies(limit=1000)
    if not all_movies:
        await callback.message.edit_text(
            t(user.language, "admin_movie_list_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, "adm:movies")]
            ),
        )
        await callback.answer()
        return

    page_items, total_pages = paginate(all_movies, page)
    lines = [
        t(
            user.language,
            "admin_movie_list_item",
            code=_esc(m.code),
            title=_esc(m.title(user.language))[:40],
            state=m.publication_state,
            views=m.view_count,
        )
        for m in page_items
    ]
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_movie_list_keyboard(page_items, user.language, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("am:view:"))
async def handle_movie_view(callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs) -> None:
    movie_id = int(callback.data.split(":")[2])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    category = await uow.catalog.get_category(movie.category_id) if movie.category_id else None
    text = t(
        user.language,
        "admin_movie_detail_title",
        title=_esc(movie.title(user.language)),
        code=_esc(movie.code),
        category=_esc(category.title_uz) if category else "—",
        access_type=movie.access_type,
        state=movie.publication_state,
        views=movie.view_count,
    )
    await callback.message.edit_text(
        text, reply_markup=admin_movie_detail_keyboard(movie, user.language)
    )
    await callback.answer()


# --- Search -----------------------------------------------------------------------


@router.callback_query(F.data == "am:search")
async def handle_movie_search_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(MovieAdminStates.awaiting_search_query)
    await callback.message.edit_text(
        t(user.language, "admin_movie_search_prompt"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:movies")]
        ),
    )
    await callback.answer()


@router.message(StateFilter(MovieAdminStates.awaiting_search_query), F.text)
async def handle_movie_search_query(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    results = await uow.catalog.search_any_state(message.text.strip())
    await state.clear()
    if not results:
        await message.answer(
            t(user.language, "admin_movie_list_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, "adm:movies")]
            ),
        )
        return
    page_items, total_pages = paginate(results, 0)
    lines = [
        t(
            user.language,
            "admin_movie_list_item",
            code=_esc(m.code),
            title=_esc(m.title(user.language))[:40],
            state=m.publication_state,
            views=m.view_count,
        )
        for m in page_items
    ]
    await message.answer(
        "\n".join(lines),
        reply_markup=admin_movie_list_keyboard(page_items, user.language, 0, total_pages),
    )


# --- Publish / Archive ------------------------------------------------------------


@router.callback_query(F.data.startswith("am:publish:"))
async def handle_movie_publish(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    movie_id = int(callback.data.split(":")[2])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await uow.catalog.update(movie, publication_state=MoviePublicationState.PUBLISHED.value)
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="publish_movie",
        entity_type="movie",
        entity_id=str(movie_id),
        after={"publication_state": "published"},
    )
    await callback.answer(
        t(user.language, "admin_movie_published", code=movie.code), show_alert=True
    )
    await handle_movie_view(callback, uow, user, **kwargs)


@router.callback_query(F.data.startswith("am:archive:"))
async def handle_movie_archive(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    movie_id = int(callback.data.split(":")[2])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await uow.catalog.update(movie, publication_state=MoviePublicationState.ARCHIVED.value)
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="archive_movie",
        entity_type="movie",
        entity_id=str(movie_id),
        after={"publication_state": "archived"},
    )
    await callback.answer(
        t(user.language, "admin_movie_archived", code=movie.code), show_alert=True
    )
    await handle_movie_view(callback, uow, user, **kwargs)


# --- Delete (with mandatory confirmation) -----------------------------------------


@router.callback_query(F.data.startswith("am:del:"))
async def handle_movie_delete_prompt(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    movie_id = int(callback.data.split(":")[2])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await callback.message.edit_text(
        t(
            user.language,
            "admin_movie_delete_confirm",
            title=_esc(movie.title(user.language)),
            code=_esc(movie.code),
        ),
        reply_markup=admin_movie_delete_confirm_keyboard(movie_id, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("am:del_confirm:"))
async def handle_movie_delete_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    movie_id = int(callback.data.split(":")[2])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    code = movie.code
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="delete_movie",
        entity_type="movie",
        entity_id=str(movie_id),
        before={"code": code, "title_uz": movie.title_uz},
    )
    await uow.catalog.delete(movie)
    await callback.message.edit_text(
        t(user.language, "admin_movie_deleted", code=_esc(code)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:movies")]
        ),
    )
    await callback.answer()


# --- Add movie: upload video -> code -> titles -> category -> access -> poster -> draft ---


@router.callback_query(F.data == "am:add")
async def handle_movie_add_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(MovieAdminStates.awaiting_video)
    await callback.message.edit_text(
        t(user.language, "admin_movie_upload_video_prompt"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:movies")]
        ),
    )
    await callback.answer()


@router.message(StateFilter(MovieAdminStates.awaiting_video))
async def handle_movie_video_received(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    if message.video is None:
        await message.answer(t(user.language, "admin_movie_invalid_video"))
        return
    await state.update_data(
        video_file_id=message.video.file_id, video_duration_seconds=message.video.duration
    )
    await state.set_state(MovieAdminStates.awaiting_code)
    await message.answer(t(user.language, "admin_movie_enter_code_prompt"))


@router.message(StateFilter(MovieAdminStates.awaiting_code), F.text)
async def handle_movie_code_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    code = message.text.strip()
    existing = await uow.catalog.get_by_code(code)
    if existing is not None:
        await message.answer(t(user.language, "admin_movie_code_taken"))
        return
    await state.update_data(code=code)
    await state.set_state(MovieAdminStates.awaiting_title_uz)
    await message.answer(t(user.language, "admin_movie_enter_title_uz"))


@router.message(StateFilter(MovieAdminStates.awaiting_title_uz), F.text)
async def handle_movie_title_uz(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title_uz=message.text.strip())
    await state.set_state(MovieAdminStates.awaiting_title_ru)
    await message.answer(t(user.language, "admin_movie_enter_title_ru"))


@router.message(StateFilter(MovieAdminStates.awaiting_title_ru), F.text)
async def handle_movie_title_ru(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title_ru=message.text.strip())
    await state.set_state(MovieAdminStates.awaiting_title_en)
    await message.answer(t(user.language, "admin_movie_enter_title_en"))


@router.message(StateFilter(MovieAdminStates.awaiting_title_en), F.text)
async def handle_movie_title_en(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.update_data(title_en=message.text.strip())
    await state.set_state(MovieAdminStates.awaiting_description_uz)
    await message.answer(t(user.language, "admin_movie_enter_description_uz"))


@router.message(StateFilter(MovieAdminStates.awaiting_description_uz), F.text)
async def handle_movie_description_uz(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    value = message.text.strip()
    await state.update_data(description_uz=None if value == "-" else value)
    await state.set_state(MovieAdminStates.awaiting_description_ru)
    await message.answer(t(user.language, "admin_movie_enter_description_ru"))


@router.message(StateFilter(MovieAdminStates.awaiting_description_ru), F.text)
async def handle_movie_description_ru(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    value = message.text.strip()
    await state.update_data(description_ru=None if value == "-" else value)
    await state.set_state(MovieAdminStates.awaiting_description_en)
    await message.answer(t(user.language, "admin_movie_enter_description_en"))


@router.message(StateFilter(MovieAdminStates.awaiting_description_en), F.text)
async def handle_movie_description_en(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    value = message.text.strip()
    await state.update_data(description_en=None if value == "-" else value)
    await state.set_state(MovieAdminStates.choosing_category)
    categories = await uow.catalog.list_all_categories()
    await message.answer(
        t(user.language, "admin_movie_choose_category_prompt"),
        reply_markup=admin_category_pick_keyboard(
            categories, user.language, callback_prefix="am:addcat:"
        ),
    )


@router.callback_query(
    StateFilter(MovieAdminStates.choosing_category), F.data.startswith("am:addcat:")
)
async def handle_movie_category_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    category_id = int(callback.data.split(":")[2])
    await state.update_data(category_id=category_id or None)
    await state.set_state(MovieAdminStates.choosing_access_type)
    await callback.message.edit_text(
        t(user.language, "admin_movie_choose_access_prompt"),
        reply_markup=admin_access_type_keyboard(user.language, callback_prefix="am:addaccess:"),
    )
    await callback.answer()


@router.callback_query(
    StateFilter(MovieAdminStates.choosing_access_type), F.data.startswith("am:addaccess:")
)
async def handle_movie_access_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    access_type = callback.data.split(":")[2]
    await state.update_data(access_type=access_type)
    await state.set_state(MovieAdminStates.awaiting_poster)
    await callback.message.edit_text(t(user.language, "admin_movie_upload_poster_prompt"))
    await callback.answer()


@router.message(StateFilter(MovieAdminStates.awaiting_poster))
async def handle_movie_poster_received(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    poster_file_id = None
    if message.photo:
        poster_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip() != "-":
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(poster_file_id=poster_file_id)
    data = await state.get_data()
    category = (
        await uow.catalog.get_category(data["category_id"]) if data.get("category_id") else None
    )
    await state.set_state(MovieAdminStates.confirming_draft)
    await message.answer(
        t(
            user.language,
            "admin_movie_draft_summary",
            code=_esc(data["code"]),
            title_uz=_esc(data["title_uz"]),
            title_ru=_esc(data["title_ru"]),
            title_en=_esc(data["title_en"]),
            category=_esc(category.title_uz) if category else "—",
            access_type=data["access_type"],
        ),
        reply_markup=admin_movie_draft_confirm_keyboard(user.language),
    )


@router.callback_query(StateFilter(MovieAdminStates.confirming_draft), F.data == "am:draft_cancel")
async def handle_movie_draft_cancel(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_action_cancelled"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:movies")]
        ),
    )
    await callback.answer()


@router.callback_query(StateFilter(MovieAdminStates.confirming_draft), F.data == "am:draft_confirm")
async def handle_movie_draft_confirm(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    movie = await uow.catalog.create(
        code=data["code"],
        title_uz=data["title_uz"],
        title_ru=data["title_ru"],
        title_en=data["title_en"],
        description_uz=data.get("description_uz"),
        description_ru=data.get("description_ru"),
        description_en=data.get("description_en"),
        category_id=data.get("category_id") or None,
        access_type=data["access_type"],
        publication_state=MoviePublicationState.DRAFT.value,
        video_file_id=data["video_file_id"],
        video_duration_seconds=data.get("video_duration_seconds"),
        poster_file_id=data.get("poster_file_id"),
        created_by_admin_id=user.id,
    )
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="create_movie_draft",
        entity_type="movie",
        entity_id=str(movie.id),
        after={"code": movie.code},
    )
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_movie_saved_draft", code=_esc(movie.code)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:movies")]
        ),
    )
    await callback.answer()


# --- Edit metadata -----------------------------------------------------------------


@router.callback_query(F.data.startswith("am:edit:"))
async def handle_movie_edit_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    movie_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        t(user.language, "admin_movie_edit_field_prompt"),
        reply_markup=admin_movie_edit_field_keyboard(movie_id, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("am:editf:"))
async def handle_movie_edit_field_chosen(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    _, _, movie_id_str, field = callback.data.split(":")
    movie_id = int(movie_id_str)
    movie = await uow.catalog.get_by_id(movie_id)
    if movie is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return

    if field == "category":
        categories = await uow.catalog.list_all_categories()
        await state.update_data(edit_movie_id=movie_id, edit_field=field)
        await callback.message.edit_text(
            t(user.language, "admin_movie_choose_category_prompt"),
            reply_markup=admin_category_pick_keyboard(
                categories, user.language, callback_prefix="am:editcatval:"
            ),
        )
        await callback.answer()
        return
    if field == "access":
        await state.update_data(edit_movie_id=movie_id, edit_field=field)
        await callback.message.edit_text(
            t(user.language, "admin_movie_choose_access_prompt"),
            reply_markup=admin_access_type_keyboard(
                user.language, callback_prefix="am:editaccval:"
            ),
        )
        await callback.answer()
        return

    await state.update_data(edit_movie_id=movie_id, edit_field=field)
    await state.set_state(MovieAdminStates.awaiting_new_field_value)
    await callback.message.edit_text(t(user.language, "admin_movie_enter_new_value_prompt"))
    await callback.answer()


@router.message(StateFilter(MovieAdminStates.awaiting_new_field_value), F.text)
async def handle_movie_new_field_value(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    movie = await uow.catalog.get_by_id(data["edit_movie_id"])
    if movie is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    field = data["edit_field"]
    before = {field: getattr(movie, field)}
    await uow.catalog.update(movie, **{field: message.text.strip()})
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="update_movie",
        entity_type="movie",
        entity_id=str(movie.id),
        before=before,
        after={field: message.text.strip()},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_movie_updated"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"am:view:{movie.id}")]
        ),
    )


@router.callback_query(F.data.startswith("am:editcatval:"))
async def handle_movie_edit_category_value(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    category_id = int(callback.data.split(":")[2])
    data = await state.get_data()
    movie = await uow.catalog.get_by_id(data["edit_movie_id"])
    if movie is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await uow.catalog.update(movie, category_id=category_id or None)
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="update_movie",
        entity_type="movie",
        entity_id=str(movie.id),
        after={"category_id": category_id or None},
    )
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_movie_updated"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"am:view:{movie.id}")]
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("am:editaccval:"))
async def handle_movie_edit_access_value(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    access_type = callback.data.split(":")[2]
    data = await state.get_data()
    movie = await uow.catalog.get_by_id(data["edit_movie_id"])
    if movie is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    await uow.catalog.update(movie, access_type=access_type)
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="update_movie",
        entity_type="movie",
        entity_id=str(movie.id),
        after={"access_type": access_type},
    )
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_movie_updated"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"am:view:{movie.id}")]
        ),
    )
    await callback.answer()


# --- Replace video / poster --------------------------------------------------------


@router.callback_query(F.data.startswith("am:replvid:"))
async def handle_movie_replace_video_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    movie_id = int(callback.data.split(":")[2])
    await state.update_data(replace_movie_id=movie_id)
    await state.set_state(MovieAdminStates.awaiting_new_video)
    await callback.message.edit_text(t(user.language, "admin_movie_upload_new_video_prompt"))
    await callback.answer()


@router.message(StateFilter(MovieAdminStates.awaiting_new_video))
async def handle_movie_replace_video_received(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    if message.video is None:
        await message.answer(t(user.language, "admin_movie_invalid_video"))
        return
    data = await state.get_data()
    movie = await uow.catalog.get_by_id(data["replace_movie_id"])
    if movie is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    await uow.catalog.update(
        movie, video_file_id=message.video.file_id, video_duration_seconds=message.video.duration
    )
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="replace_movie_video",
        entity_type="movie",
        entity_id=str(movie.id),
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_movie_video_replaced"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"am:view:{movie.id}")]
        ),
    )


@router.callback_query(F.data.startswith("am:replpost:"))
async def handle_movie_replace_poster_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    movie_id = int(callback.data.split(":")[2])
    await state.update_data(replace_movie_id=movie_id)
    await state.set_state(MovieAdminStates.awaiting_new_poster)
    await callback.message.edit_text(t(user.language, "admin_movie_upload_new_poster_prompt"))
    await callback.answer()


@router.message(StateFilter(MovieAdminStates.awaiting_new_poster))
async def handle_movie_replace_poster_received(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    if not message.photo:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    data = await state.get_data()
    movie = await uow.catalog.get_by_id(data["replace_movie_id"])
    if movie is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    await uow.catalog.update(movie, poster_file_id=message.photo[-1].file_id)
    await uow.audit.record(
        admin_id=None,
        admin_username=f"tg:{user.telegram_id}",
        action="replace_movie_poster",
        entity_type="movie",
        entity_id=str(movie.id),
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_movie_poster_replaced"),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, f"am:view:{movie.id}")]
        ),
    )
