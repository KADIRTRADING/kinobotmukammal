"""Telegram-side Admin Panel: movie management (video upload/MovieAdminStates,
delete), statistics, mandatory channels management, broadcasting, promo code
generator, and one-click Web Admin Panel launching.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import secrets
from typing import Any

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.admin.security import create_session_token, hash_password
from app.bot.keyboards.admin import (
    admin_access_type_inline_keyboard,
    admin_cancel_inline_keyboard,
    admin_categories_inline_keyboard,
    admin_channels_inline_keyboard,
    admin_confirm_inline_keyboard,
    admin_main_inline_keyboard,
    admin_promo_type_inline_keyboard,
)
from app.bot.states import AdminPanelStates, MovieAdminStates
from app.config import get_settings
from app.db.models.admin import Admin
from app.db.models.catalog import MandatoryChannel
from app.db.models.enums import AdminRole, MovieAccessType, MoviePublicationState, PromoKind
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork
from app.services.promo_service import PromoService

router = Router(name="admin_panel")
settings = get_settings()


async def get_or_create_admin(
    telegram_id: int, uow: UnitOfWork, username: str | None = None
) -> Admin | None:
    """Returns the Admin record for a Telegram user if they are an active admin
    or part of BOOTSTRAP_SUPERADMIN_IDS (auto-creating their DB record if needed)."""
    admin = await uow.admins.get_by_telegram_id(telegram_id)
    if admin is not None and admin.is_active:
        return admin

    if telegram_id in settings.bootstrap_superadmin_ids:
        if admin is None:
            uname = username or f"superadmin_{telegram_id}"
            if await uow.admins.get_by_username(uname):
                uname = f"{uname}_{telegram_id}"
            admin = await uow.admins.create(
                username=uname,
                password_hash=hash_password(secrets.token_urlsafe(16)),
                telegram_id=telegram_id,
                role=AdminRole.SUPERADMIN.value,
                is_active=True,
            )
            await uow.session.commit()
        return admin

    return None


async def is_admin_user(telegram_id: int, uow: UnitOfWork) -> bool:
    admin = await get_or_create_admin(telegram_id, uow)
    return admin is not None and admin.is_active


def _build_web_url(admin_id: int) -> str:
    token = create_session_token(admin_id)
    base = settings.public_base_url.rstrip("/")
    return f"{base}/admin/auth/telegram?token={token}"


# --- /admin Entrypoint --------------------------------------------------------


@router.message(Command("admin"))
@router.message(F.text.in_({"👑 Admin Panel", "Admin panel", "/admin"}))
async def handle_admin_command(message: Message, uow: UnitOfWork, state: FSMContext) -> None:
    admin = await get_or_create_admin(message.from_user.id, uow, message.from_user.username)
    if not admin:
        return

    await state.clear()
    web_url = _build_web_url(admin.id)
    text = (
        "🎬 <b>Movie Bot — Admin Panel</b>\n\n"
        f"Xush kelibsiz, <b>{admin.username}</b>!\n"
        "Quyidagi boshqaruv bo'limlaridan birini tanlang:"
    )
    await message.answer(
        text,
        reply_markup=admin_main_inline_keyboard(web_app_url=web_url, browser_url=web_url),
    )


@router.callback_query(F.data == "admin:menu")
async def handle_admin_menu_callback(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    admin = await get_or_create_admin(callback.from_user.id, uow, callback.from_user.username)
    if not admin:
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    await state.clear()
    web_url = _build_web_url(admin.id)
    text = (
        "🎬 <b>Movie Bot — Admin Panel</b>\n\n"
        f"Xush kelibsiz, <b>{admin.username}</b>!\n"
        "Quyidagi boshqaruv bo'limlaridan birini tanlang:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=admin_main_inline_keyboard(web_app_url=web_url, browser_url=web_url),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:close")
async def handle_admin_close(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Admin panel yopildi. ✅")
    await callback.answer()


@router.callback_query(F.data == "admin:cancel")
@router.message(Command("cancel"))
async def handle_admin_cancel(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = "❌ Bekor qilindi."
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text)
        await event.answer()
    else:
        await event.answer(text)


# --- 📊 Statistics ------------------------------------------------------------


@router.callback_query(F.data == "admin:stats")
async def handle_admin_stats(callback: CallbackQuery, uow: UnitOfWork) -> None:
    if not await is_admin_user(callback.from_user.id, uow):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    total_users = await uow.users.count_all()
    today_users = await uow.users.count_today_users()
    premium_users = await uow.users.count_premium_users()
    total_movies = await uow.catalog.count_movies()
    total_channels = await uow.catalog.count_channels()

    text = (
        "📊 <b>Bot Statistikasi</b>\n\n"
        f"👤 <b>Jami foydalanuvchilar:</b> {total_users:,}\n"
        f"📈 <b>Bugun qo'shilganlar:</b> {today_users:,}\n"
        f"⭐ <b>Premium foydalanuvchilar:</b> {premium_users:,}\n"
        f"🎬 <b>Jami kinolar:</b> {total_movies:,}\n"
        f"📢 <b>Majburiy kanallar:</b> {total_channels:,}\n\n"
        f"🕒 <i>Yangilangan vaqt: {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M UTC')}</i>"
    )
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin:stats")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu")],
        ]
    )
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


# --- 🎬 Movie Add Flow (MovieAdminStates) -------------------------------------


@router.callback_query(F.data == "admin:movie:add")
async def handle_movie_add_start(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    if not await is_admin_user(callback.from_user.id, uow):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    await state.set_state(MovieAdminStates.awaiting_video)
    text = (
        "🎬 <b>Kino qo'shish</b>\n\n"
        "Iltimos, kino videosini yuboring yoki boshqa kanaldan forward qiling:\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing yoki quyidagi tugmani bosing.</i>"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_inline_keyboard())
    await callback.answer()


@router.message(F.video | F.document)
async def handle_video_received(message: Message, uow: UnitOfWork, state: FSMContext) -> None:
    """Captures video uploads from admins either during awaiting_video or directly."""
    if message.chat.type != "private":
        return
    if not await is_admin_user(message.from_user.id, uow):
        return

    video_file_id = None
    if message.video:
        video_file_id = message.video.file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("video/"):
        video_file_id = message.document.file_id

    if not video_file_id:
        return

    await state.set_state(MovieAdminStates.awaiting_code)
    await state.update_data(video_file_id=video_file_id)

    text = (
        "✅ <b>Kino videosi qabul qilindi!</b>\n\n"
        "Endi kino kodini kiriting (faqat raqamlar, masalan: <code>105</code>):"
    )
    await message.answer(text, reply_markup=admin_cancel_inline_keyboard())


@router.message(MovieAdminStates.awaiting_code, F.text)
async def handle_movie_code_input(message: Message, uow: UnitOfWork, state: FSMContext) -> None:
    code = message.text.strip()
    if not code.isdigit():
        await message.answer("⚠️ Kod faqat raqamlardan iborat bo'lishi kerak. Qayta kiriting:")
        return

    existing = await uow.catalog.get_by_code(code)
    if existing:
        await message.answer(
            f"⚠️ <b>{code}</b> kodi allaqachon mavjud ({existing.title_uz})!\n"
            "Boshqa kod kiriting:"
        )
        return

    await state.update_data(code=code)
    await state.set_state(MovieAdminStates.awaiting_title_uz)
    await message.answer(
        "Kino nomini kiriting (O'zbek tilida):",
        reply_markup=admin_cancel_inline_keyboard(),
    )


@router.message(MovieAdminStates.awaiting_title_uz, F.text)
async def handle_movie_title_uz(message: Message, state: FSMContext) -> None:
    title_uz = message.text.strip()
    await state.update_data(title_uz=title_uz)
    await state.set_state(MovieAdminStates.awaiting_title_ru)
    await message.answer(
        "Kino nomini kiriting (Rus tilida yoki o'tkazib yuborish uchun /skip deb yozing):",
        reply_markup=admin_cancel_inline_keyboard(),
    )


@router.message(MovieAdminStates.awaiting_title_ru, F.text)
async def handle_movie_title_ru(message: Message, state: FSMContext) -> None:
    title_ru = None if message.text.strip().lower() == "/skip" else message.text.strip()
    await state.update_data(title_ru=title_ru)
    await state.set_state(MovieAdminStates.awaiting_title_en)
    await message.answer(
        "Kino nomini kiriting (Ingliz tilida yoki o'tkazib yuborish uchun /skip deb yozing):",
        reply_markup=admin_cancel_inline_keyboard(),
    )


@router.message(MovieAdminStates.awaiting_title_en, F.text)
async def handle_movie_title_en(message: Message, state: FSMContext) -> None:
    title_en = None if message.text.strip().lower() == "/skip" else message.text.strip()
    await state.update_data(title_en=title_en)
    await state.set_state(MovieAdminStates.awaiting_poster)
    await message.answer(
        "Kino uchun poster (rasm) yuboring yoki o'tkazib yuborish uchun /skip deb yozing:",
        reply_markup=admin_cancel_inline_keyboard(),
    )


@router.message(MovieAdminStates.awaiting_poster)
async def handle_movie_poster(message: Message, uow: UnitOfWork, state: FSMContext) -> None:
    poster_file_id = None
    if message.photo:
        poster_file_id = message.photo[-1].file_id
    elif message.text and message.text.strip().lower() == "/skip":
        poster_file_id = None

    await state.update_data(poster_file_id=poster_file_id)
    categories = await uow.catalog.list_active_categories()

    await state.set_state(MovieAdminStates.choosing_category)
    await message.answer(
        "Kino toifasini (kategoriyasini) tanlang:",
        reply_markup=admin_categories_inline_keyboard(categories),
    )


@router.callback_query(MovieAdminStates.choosing_category, F.data.startswith("admin:cat:"))
async def handle_movie_category_selected(callback: CallbackQuery, state: FSMContext) -> None:
    cat_part = callback.data.split(":")[2]
    category_id = int(cat_part) if cat_part != "none" else None
    await state.update_data(category_id=category_id)

    await state.set_state(MovieAdminStates.choosing_access_type)
    text = (
        "Kino kirish turini tanlang:\n\n"
        "🟢 <b>Bepul (FREE)</b> — barcha obuna bo'lgan foydalanuvchilar ko'ra oladi.\n"
        "⭐ <b>Premium</b> — faqat faol Premium obunachilar ko'ra oladi."
    )
    await callback.message.edit_text(text, reply_markup=admin_access_type_inline_keyboard())
    await callback.answer()


@router.callback_query(MovieAdminStates.choosing_access_type, F.data.startswith("admin:access:"))
async def handle_movie_access_selected(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    access_type = callback.data.split(":")[2]  # "free" or "premium"
    data = await state.get_data()
    await state.clear()

    title_uz = data["title_uz"]
    title_ru = data.get("title_ru") or title_uz
    title_en = data.get("title_en") or title_uz

    movie = await uow.catalog.create(
        code=data["code"],
        title_uz=title_uz,
        title_ru=title_ru,
        title_en=title_en,
        video_file_id=data["video_file_id"],
        poster_file_id=data.get("poster_file_id"),
        category_id=data.get("category_id"),
        access_type=access_type,
        publication_state=MoviePublicationState.PUBLISHED.value,
    )
    await uow.session.commit()

    text = (
        "✅ <b>Kino muvaffaqiyatli saqlandi va e'lon qilindi!</b>\n\n"
        f"🔢 <b>Kodi:</b> <code>{movie.code}</code>\n"
        f"🎬 <b>Nomi:</b> {movie.title_uz}\n"
        f"💎 <b>Kirish turi:</b> {access_type.upper()}\n\n"
        "Foydalanuvchilar endi ushbu kod orqali kinoni tomosha qilishlari mumkin."
    )
    await callback.message.edit_text(text)
    await callback.answer("Kino saqlandi! ✅")


# --- 🗑 Movie Delete Flow -----------------------------------------------------


@router.callback_query(F.data == "admin:movie:delete")
async def handle_movie_delete_start(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    if not await is_admin_user(callback.from_user.id, uow):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    await state.set_state(AdminPanelStates.awaiting_delete_code)
    text = (
        "🗑 <b>Kino o'chirish</b>\n\n"
        "O'chirmoqchi bo'lgan kino kodini kiriting:\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_inline_keyboard())
    await callback.answer()


@router.message(AdminPanelStates.awaiting_delete_code, F.text)
async def handle_movie_delete_code_input(
    message: Message, uow: UnitOfWork, state: FSMContext
) -> None:
    code = message.text.strip()
    movie = await uow.catalog.get_by_code(code)
    if not movie:
        await message.answer(
            f"❌ <b>{code}</b> kodli kino topilmadi. Qayta kiriting yoki /cancel yozing:"
        )
        return

    text = (
        f"🎬 <b>{movie.title_uz}</b> (Kod: <code>{movie.code}</code>)\n"
        f"👁 Ko'rishlar soni: {movie.view_count}\n\n"
        "Haqiqatan ham ushbu kinoni butunlay o'chirib tashlamoqchimisiz?"
    )
    await message.answer(
        text,
        reply_markup=admin_confirm_inline_keyboard(
            f"admin:confirm_del_movie:{movie.id}", "admin:cancel"
        ),
    )


@router.callback_query(F.data.startswith("admin:confirm_del_movie:"))
async def handle_movie_delete_confirm(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    movie_id = int(callback.data.split(":")[2])
    movie = await uow.catalog.get_by_id(movie_id)
    if movie:
        await uow.catalog.delete(movie)
        await uow.session.commit()

    await state.clear()
    await callback.message.edit_text("✅ Kino muvaffaqiyatli o'chirildi!")
    await callback.answer()


# --- 📢 Mandatory Channels Management -----------------------------------------


@router.callback_query(F.data == "admin:channels")
async def handle_admin_channels(callback: CallbackQuery, uow: UnitOfWork) -> None:
    if not await is_admin_user(callback.from_user.id, uow):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    channels = await uow.catalog.list_all_channels()
    if not channels:
        text = "📢 <b>Majburiy obuna kanallari</b>\n\nHozircha kanallar qo'shilmagan."
    else:
        text = "📢 <b>Majburiy obuna kanallari:</b>\n\n"
        for i, ch in enumerate(channels, 1):
            status = "✅ Bot admin" if ch.bot_is_admin_verified else "❌ Bot admin emas!"
            active = "Faol" if ch.is_active else "Nofaol"
            text += f"{i}. <b>{ch.title}</b> ({ch.chat_id})\n   Holat: {status} | {active}\n"

    await callback.message.edit_text(text, reply_markup=admin_channels_inline_keyboard(channels))
    await callback.answer()


@router.callback_query(F.data == "admin:channel:add")
async def handle_admin_channel_add_start(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    if not await is_admin_user(callback.from_user.id, uow):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    await state.set_state(AdminPanelStates.awaiting_channel_add)
    text = (
        "📢 <b>Kanal qo'shish</b>\n\n"
        "Kanalning @username sini (masalan: <code>@kinolar_olami</code>) yoki "
        "ID sini (masalan: <code>-100123456789</code>) yuboring:\n\n"
        "<i>Eslatma: Bot avval kanalda administrator huquqlariga ega bo'lishi kerak!</i>"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_inline_keyboard())
    await callback.answer()


@router.message(AdminPanelStates.awaiting_channel_add, F.text)
async def handle_admin_channel_input(
    message: Message, uow: UnitOfWork, state: FSMContext
) -> None:
    raw_chat = message.text.strip()
    chat_id = raw_chat
    if chat_id.startswith("https://t.me/"):
        rest = chat_id[len("https://t.me/") :]
        if not rest.startswith(("+", "joinchat/")):
            chat_id = f"@{rest.split('/')[0]}"

    bot = message.bot
    bot_user = await bot.get_me()

    is_admin = False
    title = chat_id
    invite_link = None

    try:
        cid = int(chat_id) if (chat_id.startswith("-") or chat_id.isdigit()) else chat_id
        chat = await bot.get_chat(chat_id=cid)
        title = chat.title or str(chat_id)
        member = await bot.get_chat_member(chat_id=cid, user_id=bot_user.id)
        is_admin = member.status in ("administrator", "creator")

        if is_admin:
            try:
                link_obj = await bot.create_chat_invite_link(chat_id=cid)
                invite_link = link_obj.invite_link
            except Exception:
                try:
                    invite_link = await bot.export_chat_invite_link(chat_id=cid)
                except Exception:
                    if chat.username:
                        invite_link = f"https://t.me/{chat.username}"
    except Exception as e:
        await message.answer(
            f"❌ Kanalni tekshirishda xatolik yuz berdi: {e}\n"
            "Iltimos, bot kanalda administrator ekanligiga va kanal chat_id/username to'g'riligiga ishonch hosil qiling."
        )
        return

    channel = await uow.catalog.get_channel_by_chat_id(str(chat_id))
    if channel:
        channel.title = title
        channel.is_active = True
        channel.bot_is_admin_verified = is_admin
        if invite_link:
            channel.invite_link = invite_link
    else:
        channel = MandatoryChannel(
            chat_id=str(chat_id),
            title=title,
            invite_link=invite_link,
            is_active=True,
            bot_is_admin_verified=is_admin,
        )
        uow.session.add(channel)

    await uow.session.commit()
    await state.clear()

    status_note = "✅ Bot kanalda admin!" if is_admin else "⚠️ Bot hali kanalda admin emas!"
    await message.answer(
        f"✅ Kanal saqlandi:\n<b>{title}</b> ({chat_id})\n{status_note}"
    )


@router.callback_query(F.data.startswith("admin:channel:del:"))
async def handle_admin_channel_delete(callback: CallbackQuery, uow: UnitOfWork) -> None:
    ch_id = int(callback.data.split(":")[3])
    channels = await uow.catalog.list_all_channels()
    target = next((c for c in channels if c.id == ch_id), None)
    if target:
        await uow.catalog.delete_channel(target)
        await uow.session.commit()

    channels = await uow.catalog.list_all_channels()
    text = "✅ Kanal o'chirildi!\n\n📢 <b>Majburiy obuna kanallari:</b>\n\n"
    for i, ch in enumerate(channels, 1):
        status = "✅ Bot admin" if ch.bot_is_admin_verified else "❌ Bot admin emas!"
        text += f"{i}. <b>{ch.title}</b> ({ch.chat_id}) — {status}\n"

    await callback.message.edit_text(text, reply_markup=admin_channels_inline_keyboard(channels))
    await callback.answer("Kanal o'chirildi")


@router.callback_query(F.data == "admin:channel:check")
async def handle_admin_channel_check(callback: CallbackQuery, uow: UnitOfWork) -> None:
    bot = callback.bot
    bot_user = await bot.get_me()
    channels = await uow.catalog.list_all_channels()

    for ch in channels:
        try:
            cid = int(ch.chat_id) if (ch.chat_id.startswith("-") or ch.chat_id.isdigit()) else ch.chat_id
            member = await bot.get_chat_member(chat_id=cid, user_id=bot_user.id)
            ch.bot_is_admin_verified = member.status in ("administrator", "creator")
        except Exception:
            ch.bot_is_admin_verified = False

    await uow.session.commit()

    text = "🔄 Huquqlar tekshirildi!\n\n📢 <b>Majburiy obuna kanallari:</b>\n\n"
    for i, ch in enumerate(channels, 1):
        status = "✅ Bot admin" if ch.bot_is_admin_verified else "❌ Bot admin emas!"
        text += f"{i}. <b>{ch.title}</b> ({ch.chat_id}) — {status}\n"

    await callback.message.edit_text(text, reply_markup=admin_channels_inline_keyboard(channels))
    await callback.answer("Tekshiruv yakunlandi")


# --- ✉️ Broadcast (Rassilka) --------------------------------------------------


@router.callback_query(F.data == "admin:broadcast")
async def handle_admin_broadcast_start(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    if not await is_admin_user(callback.from_user.id, uow):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    await state.set_state(AdminPanelStates.awaiting_broadcast_content)
    text = (
        "✉️ <b>Barcha foydalanuvchilarga xabar yuborish</b>\n\n"
        "Yubormoqchi bo'lgan xabaringizni yuboring (matn, rasm, video yoki kanaldan forward post):\n\n"
        "<i>Bekor qilish uchun /cancel deb yozing.</i>"
    )
    await callback.message.edit_text(text, reply_markup=admin_cancel_inline_keyboard())
    await callback.answer()


@router.message(AdminPanelStates.awaiting_broadcast_content)
async def handle_admin_broadcast_content(message: Message, state: FSMContext) -> None:
    await state.update_data(
        broadcast_chat_id=message.chat.id,
        broadcast_message_id=message.message_id,
    )
    await state.set_state(AdminPanelStates.awaiting_broadcast_confirm)

    await message.copy_to(chat_id=message.chat.id)
    await message.answer(
        "Yuqoridagi xabarni <b>barcha bot foydalanuvchilariga</b> yuborishni tasdiqlaysizmi?",
        reply_markup=admin_confirm_inline_keyboard("admin:broadcast:confirm", "admin:cancel"),
    )


async def _run_broadcast(bot: Bot, admin_id: int, from_chat_id: int, message_id: int) -> None:
    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        users = await uow.users.iter_broadcast_targets()
        user_ids = [u.telegram_id for u in users]

    total = len(user_ids)
    success = 0
    blocked = 0
    failed = 0

    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=from_chat_id, message_id=message_id)
            success += 1
        except TelegramForbiddenError:
            blocked += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # 20 messages / sec rate limit

    try:
        report = (
            "📊 <b>Xabar yuborish yakunlandi:</b>\n\n"
            f"👥 Jami qabul qiluvchilar: {total}\n"
            f"✅ Yetkazildi: {success}\n"
            f"🚫 Botni bloklagan: {blocked}\n"
            f"⚠️ Xatolar: {failed}"
        )
        await bot.send_message(chat_id=admin_id, text=report)
    except Exception:
        pass


@router.callback_query(F.data == "admin:broadcast:confirm")
async def handle_admin_broadcast_confirm(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    data = await state.get_data()
    await state.clear()

    from_chat_id = data.get("broadcast_chat_id")
    message_id = data.get("broadcast_message_id")
    if not from_chat_id or not message_id:
        await callback.message.edit_text("❌ Xabar topilmadi.")
        return

    total = await uow.users.count_all()
    asyncio.create_task(
        _run_broadcast(
            bot=callback.bot,
            admin_id=callback.from_user.id,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )
    )

    await callback.message.edit_text(
        f"🚀 <b>Xabar yuborish boshlandi!</b>\n\n"
        f"Jami qabul qiluvchilar: {total:,} ta foydalanuvchi.\n"
        "Xabar yuborish yakunlangach, sizga to'liq hisobot keladi."
    )
    await callback.answer("Yuborish boshlandi")


# --- 🎟 Promo Code Generator --------------------------------------------------


@router.callback_query(F.data == "admin:promo")
async def handle_admin_promo_start(
    callback: CallbackQuery, uow: UnitOfWork, state: FSMContext
) -> None:
    if not await is_admin_user(callback.from_user.id, uow):
        await callback.answer("Ruxsat yo'q", show_alert=True)
        return

    await state.set_state(AdminPanelStates.awaiting_promo_type)
    text = "🎟 <b>Promo kod yaratish</b>\n\nPromo kod turini tanlang:"
    await callback.message.edit_text(text, reply_markup=admin_promo_type_inline_keyboard())
    await callback.answer()


@router.callback_query(AdminPanelStates.awaiting_promo_type, F.data.startswith("admin:promo:type:"))
async def handle_admin_promo_type(callback: CallbackQuery, state: FSMContext) -> None:
    promo_type = callback.data.split(":")[3]  # "full_premium" or "discount"
    await state.update_data(promo_type=promo_type)

    if promo_type == "full_premium":
        await state.update_data(promo_value=0)
        await state.set_state(AdminPanelStates.awaiting_promo_uses)
        text = "Maksimal foydalanishlar sonini kiriting (masalan: <code>50</code>):"
    else:
        await state.set_state(AdminPanelStates.awaiting_promo_value)
        text = "Chegirma foizini kiriting (1 dan 100 gacha, masalan: <code>30</code>):"

    await callback.message.edit_text(text, reply_markup=admin_cancel_inline_keyboard())
    await callback.answer()


@router.message(AdminPanelStates.awaiting_promo_value, F.text)
async def handle_admin_promo_value(message: Message, state: FSMContext) -> None:
    val = message.text.strip()
    if not val.isdigit() or not (1 <= int(val) <= 100):
        await message.answer("⚠️ Iltimos, 1 dan 100 gacha bo'lgan foiz kiriting:")
        return

    await state.update_data(promo_value=int(val))
    await state.set_state(AdminPanelStates.awaiting_promo_uses)
    await message.answer(
        "Maksimal foydalanishlar sonini kiriting (masalan: <code>50</code>):",
        reply_markup=admin_cancel_inline_keyboard(),
    )


@router.message(AdminPanelStates.awaiting_promo_uses, F.text)
async def handle_admin_promo_uses(
    message: Message, uow: UnitOfWork, state: FSMContext
) -> None:
    uses = message.text.strip()
    if not uses.isdigit() or int(uses) <= 0:
        await message.answer("⚠️ Iltimos, musbat son kiriting:")
        return

    data = await state.get_data()
    await state.clear()

    promo_type = data["promo_type"]
    val = data.get("promo_value", 0)
    max_uses = int(uses)

    plans = await uow.plans.list_active()
    if not plans:
        # Fallback if no plan exists yet: fetch any plan or inform
        all_plans = await uow.plans.list_all()
        plan = all_plans[0] if all_plans else None
    else:
        plan = plans[0]

    if not plan:
        await message.answer(
            "⚠️ Hozircha hech qanday Premium tarif rejasi mavjud emas. Avval admin panelda reja yarating."
        )
        return

    promo_service = PromoService(uow)
    if promo_type == "full_premium":
        promo = await promo_service.create_admin_code(
            plan=plan,
            kind=PromoKind.FULL_PREMIUM,
            discount_percent=0,
            activations=max_uses,
        )
        desc = f"⭐ 100% Bepul Premium ({plan.title_uz})"
    else:
        discount = min(val, plan.max_discount_percent or 100)
        promo = await promo_service.create_admin_code(
            plan=plan,
            kind=PromoKind.PERCENT_DISCOUNT,
            discount_percent=discount,
            activations=max_uses,
        )
        desc = f"🏷 {discount}% Chegirma ({plan.title_uz})"

    await uow.session.commit()

    text = (
        "✅ <b>Yangi promo kod yaratildi!</b>\n\n"
        f"🎟 Kod: <code>{promo.code}</code>\n"
        f"🎁 Turi: {desc}\n"
        f"👥 Maksimal faollashtirishlar: {max_uses}\n\n"
        "Foydalanuvchilar ushbu kodni botda faollashtirishlari mumkin."
    )
    await message.answer(text)
