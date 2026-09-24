"""Admin Bloggers section: review pending blogger applications, approve/
reject with a reason, inspect active blogger profiles (suspend/
reactivate), review suspicious referral activity, and configure the
global blogger acquisition-reward rate per 1000 qualified joins.

Every decision reuses `BloggerService`/`SettingsService` -- the same
services the application/referral flows use -- so admin approvals create
a `BloggerProfile` through the exact same code path as everywhere else.
"""

from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.bot.handlers.admin.audit_helper import record_admin_action
from app.bot.keyboards.admin_bloggers import (
    admin_blogger_active_list_keyboard,
    admin_blogger_application_keyboard,
    admin_blogger_pending_list_keyboard,
    admin_blogger_profile_keyboard,
    admin_bloggers_menu_keyboard,
)
from app.bot.keyboards.admin_common import admin_back_row, paginate
from app.bot.states import AdminBloggerStates
from app.db.models.user import User
from app.db.uow import UnitOfWork
from app.i18n import t
from app.services.blogger_service import BloggerService
from app.services.settings_service import SettingsService

router = Router(name="admin_bloggers")


def _esc(text: str | None) -> str:
    return html.escape(text or "")


def _user_label(target: User) -> str:
    return f"@{target.username}" if target.username else str(target.telegram_id)


@router.callback_query(F.data == "adm:bloggers")
async def handle_bloggers_menu(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.clear()
    await callback.message.edit_text(
        t(user.language, "admin_bloggers_menu_title"),
        reply_markup=admin_bloggers_menu_keyboard(user.language),
    )
    await callback.answer()


# --- Pending applications --------------------------------------------------------


@router.callback_query(F.data.startswith("ab:pending:"))
async def handle_bloggers_pending_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    page = int(callback.data.split(":")[2])
    applications = await uow.bloggers.list_pending(limit=1000)
    if not applications:
        await callback.message.edit_text(
            t(user.language, "admin_bloggers_pending_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, "adm:bloggers")]
            ),
        )
        await callback.answer()
        return
    page_items, total_pages = paginate(applications, page)
    lines = [f"#{a.id} ({_esc(a.platform_name)})" for a in page_items]
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_blogger_pending_list_keyboard(
            page_items, user.language, page, total_pages
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ab:view:"))
async def handle_blogger_application_view(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    application_id = int(callback.data.split(":")[2])
    application = await uow.bloggers.get_application(application_id)
    if application is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    applicant = await uow.users.get_by_id(application.applicant_user_id)
    applicant_label = _user_label(applicant) if applicant else str(application.applicant_user_id)
    await callback.message.edit_text(
        t(
            user.language,
            "admin_blogger_application_item",
            applicant=_esc(applicant_label),
            platform=_esc(application.platform_name),
            url=_esc(application.submitted_url),
            phrase=_esc(application.verification_phrase),
        ),
        reply_markup=admin_blogger_application_keyboard(application.id, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ab:approve:"))
async def handle_blogger_approve(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    application_id = int(callback.data.split(":")[2])
    application = await uow.bloggers.get_application(application_id)
    if application is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    applicant = await uow.users.get_by_id(application.applicant_user_id)
    await BloggerService(uow).decide(application, approve=True, admin_id=user.id)
    await record_admin_action(
        uow,
        user,
        action="approve_blogger_application",
        entity_type="blogger_application",
        entity_id=str(application_id),
    )
    label = _user_label(applicant) if applicant else str(application.applicant_user_id)
    await callback.answer(
        t(user.language, "admin_blogger_approved", applicant=label), show_alert=True
    )

    if applicant is not None:
        try:
            await callback.bot.send_message(
                chat_id=applicant.telegram_id, text=t(applicant.language, "blogger_apply_approved")
            )
        except Exception:
            pass

    await callback.message.edit_text(
        t(user.language, "admin_bloggers_menu_title"),
        reply_markup=admin_bloggers_menu_keyboard(user.language),
    )


@router.callback_query(F.data.startswith("ab:reject:"))
async def handle_blogger_reject_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    application_id = int(callback.data.split(":")[2])
    await state.update_data(application_id=application_id)
    await state.set_state(AdminBloggerStates.awaiting_reject_reason)
    await callback.message.edit_text(t(user.language, "admin_blogger_reject_reason_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminBloggerStates.awaiting_reject_reason), F.text)
async def handle_blogger_reject_reason(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    application = await uow.bloggers.get_application(data["application_id"])
    if application is None:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    reason = message.text.strip()
    applicant = await uow.users.get_by_id(application.applicant_user_id)
    await BloggerService(uow).decide(application, approve=False, admin_id=user.id, reason=reason)
    await record_admin_action(
        uow,
        user,
        action="reject_blogger_application",
        entity_type="blogger_application",
        entity_id=str(application.id),
        note=reason,
    )
    label = _user_label(applicant) if applicant else str(application.applicant_user_id)
    await state.clear()
    await message.answer(
        t(user.language, "admin_blogger_rejected", applicant=_esc(label)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:bloggers")]
        ),
    )

    if applicant is not None:
        try:
            await message.bot.send_message(
                chat_id=applicant.telegram_id,
                text=t(applicant.language, "blogger_apply_rejected", reason=reason),
            )
        except Exception:
            pass


# --- Active blogger profiles ------------------------------------------------------


@router.callback_query(F.data.startswith("ab:active:"))
async def handle_bloggers_active_list(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    page = int(callback.data.split(":")[2])
    profiles = await uow.bloggers.list_all(limit=1000)
    if not profiles:
        await callback.message.edit_text(
            t(user.language, "admin_bloggers_active_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, "adm:bloggers")]
            ),
        )
        await callback.answer()
        return
    page_items, total_pages = paginate(profiles, page)
    lines = [
        t(
            user.language,
            "admin_blogger_active_item",
            label=f"user #{p.user_id}",
            joins=p.qualified_joins_counted,
        )
        for p in page_items
    ]
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=admin_blogger_active_list_keyboard(
            page_items, user.language, page, total_pages
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ab:activeview:"))
async def handle_blogger_profile_view(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    target_user_id = int(callback.data.split(":")[2])
    profile = await uow.bloggers.get_profile_by_user(target_user_id)
    if profile is None:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    target = await uow.users.get_by_id(target_user_id)
    label = _user_label(target) if target else str(target_user_id)
    await callback.message.edit_text(
        t(
            user.language,
            "admin_blogger_active_item",
            label=_esc(label),
            joins=profile.qualified_joins_counted,
        ),
        reply_markup=admin_blogger_profile_keyboard(profile, user.language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ab:suspend:"))
async def handle_blogger_suspend_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    target_user_id = int(callback.data.split(":")[2])
    await state.update_data(blogger_user_id=target_user_id)
    await state.set_state(AdminBloggerStates.awaiting_suspend_reason)
    await callback.message.edit_text(t(user.language, "admin_blogger_suspend_reason_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminBloggerStates.awaiting_suspend_reason), F.text)
async def handle_blogger_suspend_reason(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    data = await state.get_data()
    target_user_id = data["blogger_user_id"]
    reason = message.text.strip()
    ok = await BloggerService(uow).suspend(target_user_id, reason)
    if not ok:
        await state.clear()
        await message.answer(t(user.language, "admin_not_found"))
        return
    target = await uow.users.get_by_id(target_user_id)
    label = _user_label(target) if target else str(target_user_id)
    await record_admin_action(
        uow,
        user,
        action="suspend_blogger",
        entity_type="blogger_profile",
        entity_id=str(target_user_id),
        note=reason,
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_blogger_suspended", label=_esc(label)),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:bloggers")]
        ),
    )


@router.callback_query(F.data.startswith("ab:reactivate:"))
async def handle_blogger_reactivate(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    target_user_id = int(callback.data.split(":")[2])
    ok = await BloggerService(uow).reactivate(target_user_id)
    if not ok:
        await callback.answer(t(user.language, "admin_not_found"), show_alert=True)
        return
    target = await uow.users.get_by_id(target_user_id)
    label = _user_label(target) if target else str(target_user_id)
    await record_admin_action(
        uow,
        user,
        action="reactivate_blogger",
        entity_type="blogger_profile",
        entity_id=str(target_user_id),
    )
    await callback.answer(
        t(user.language, "admin_blogger_reactivated", label=label), show_alert=True
    )
    await handle_blogger_profile_view(callback, uow, user, **kwargs)


# --- Suspicious referral activity -------------------------------------------------


@router.callback_query(F.data.startswith("ab:suspicious:"))
async def handle_suspicious_referrals(
    callback: CallbackQuery, uow: UnitOfWork, user: User, **kwargs
) -> None:
    page = int(callback.data.split(":")[2])
    suspicious = await uow.referrals.list_suspicious(limit=1000)
    if not suspicious:
        await callback.message.edit_text(
            t(user.language, "admin_bloggers_suspicious_empty"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[admin_back_row(user.language, "adm:bloggers")]
            ),
        )
        await callback.answer()
        return
    page_items, total_pages = paginate(suspicious, page)
    lines = [
        t(
            user.language,
            "admin_suspicious_referral_item",
            referrer=r.referrer_user_id,
            referred=r.referred_user_id,
            reason=_esc(r.suspicious_reason),
            date=r.attributed_at.strftime("%Y-%m-%d"),
        )
        for r in page_items
    ]
    from app.bot.keyboards.admin_common import admin_pagination_row

    nav = admin_pagination_row(
        user.language, prefix="ab:suspicious:", page=page, total_pages=total_pages
    )
    rows = [nav] if nav else []
    rows.append(admin_back_row(user.language, "adm:bloggers"))
    await callback.message.edit_text(
        "\n\n".join(lines), reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await callback.answer()


# --- Global acquisition reward rate -----------------------------------------------


@router.callback_query(F.data == "ab:rate")
async def handle_reward_rate_start(
    callback: CallbackQuery, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    await state.set_state(AdminBloggerStates.awaiting_reward_rate)
    await callback.message.edit_text(t(user.language, "admin_reward_rate_prompt"))
    await callback.answer()


@router.message(StateFilter(AdminBloggerStates.awaiting_reward_rate), F.text)
async def handle_reward_rate_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    try:
        rate = int(message.text.strip())
        if rate < 0:
            raise ValueError
    except ValueError:
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    await state.update_data(reward_rate=rate)
    await state.set_state(AdminBloggerStates.awaiting_reward_currency)
    await message.answer(t(user.language, "admin_reward_rate_currency_prompt"))


@router.message(StateFilter(AdminBloggerStates.awaiting_reward_currency), F.text)
async def handle_reward_currency_entered(
    message: Message, uow: UnitOfWork, user: User, state: FSMContext, **kwargs
) -> None:
    currency = message.text.strip().upper()
    if not (2 <= len(currency) <= 8):
        await message.answer(t(user.language, "admin_invalid_input"))
        return
    data = await state.get_data()
    rate = data["reward_rate"]
    await SettingsService(uow).set_global_blogger_reward_per_1000(rate, currency)
    await record_admin_action(
        uow,
        user,
        action="update_blogger_reward_rate",
        entity_type="settings",
        after={"rate": rate, "currency": currency},
    )
    await state.clear()
    await message.answer(
        t(user.language, "admin_reward_rate_updated", rate=rate, currency=currency),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[admin_back_row(user.language, "adm:bloggers")]
        ),
    )
