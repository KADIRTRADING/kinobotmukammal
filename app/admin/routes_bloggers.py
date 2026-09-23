"""Blogger application review + acquisition reward rate configuration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.blogger_service import BloggerService
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/admin/bloggers", tags=["admin-bloggers"])


@router.get("", response_class=HTMLResponse)
async def list_bloggers(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    pending_applications = await uow.bloggers.list_pending()
    profiles = await uow.bloggers.list_all()
    settings_service = SettingsService(uow)
    global_rate, global_currency = await settings_service.global_blogger_reward_per_1000()
    return templates.TemplateResponse(
        "bloggers.html",
        {
            "request": request,
            "pending_applications": pending_applications,
            "profiles": profiles,
            "global_rate": global_rate,
            "global_currency": global_currency,
        },
    )


@router.post("/settings/reward_rate")
async def update_reward_rate(
    rate: int = Form(...),
    currency: str = Form("UZS"),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    await SettingsService(uow).set_global_blogger_reward_per_1000(rate, currency)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="update_global_blogger_reward_rate",
        entity_type="settings",
        after={"rate": rate, "currency": currency},
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)


@router.post("/applications/{application_id}/approve")
async def approve_application(
    application_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    application = await uow.bloggers.get_application(application_id)
    if application is None:
        return RedirectResponse(url="/admin/bloggers", status_code=302)
    blogger_service = BloggerService(uow)
    await blogger_service.decide(application, approve=True, admin_id=admin.id)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="approve_blogger_application",
        entity_type="blogger_application",
        entity_id=str(application_id),
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)


@router.post("/applications/{application_id}/reject")
async def reject_application(
    application_id: int,
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    application = await uow.bloggers.get_application(application_id)
    if application is None:
        return RedirectResponse(url="/admin/bloggers", status_code=302)
    blogger_service = BloggerService(uow)
    await blogger_service.decide(application, approve=False, admin_id=admin.id, reason=reason)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="reject_blogger_application",
        entity_type="blogger_application",
        entity_id=str(application_id),
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)


@router.post("/{blogger_user_id}/suspend")
async def suspend_blogger(
    blogger_user_id: int,
    reason: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    blogger_service = BloggerService(uow)
    await blogger_service.suspend(blogger_user_id, reason)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="suspend_blogger",
        entity_type="blogger_profile",
        entity_id=str(blogger_user_id),
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)


@router.post("/{blogger_user_id}/reactivate")
async def reactivate_blogger(
    blogger_user_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    blogger_service = BloggerService(uow)
    await blogger_service.reactivate(blogger_user_id)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="reactivate_blogger",
        entity_type="blogger_profile",
        entity_id=str(blogger_user_id),
    )
    await session.commit()
    return RedirectResponse(url="/admin/bloggers", status_code=302)
