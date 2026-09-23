"""Broadcast composer: preview/confirm/queue. Actual sending happens in
`app.workers.broadcast_worker`; this route only creates the draft, resolves
the recipient snapshot, and marks it QUEUED."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole, BroadcastTarget
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.broadcast_service import BroadcastService

router = APIRouter(prefix="/admin/broadcasts", tags=["admin-broadcasts"])


@router.get("", response_class=HTMLResponse)
async def list_broadcasts(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    active = await uow.broadcasts.list_queued_or_running()
    return templates.TemplateResponse("broadcasts.html", {"request": request, "active": active})


@router.post("/create")
async def create_broadcast(
    target: str = Form(...),
    text_uz: str = Form(...),
    text_ru: str = Form(...),
    text_en: str = Form(...),
    rate_limit_per_second: int = Form(20),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    broadcast_service = BroadcastService(uow)
    broadcast = await broadcast_service.create_draft(
        admin_id=admin.id,
        target=BroadcastTarget(target),
        text_uz=text_uz,
        text_ru=text_ru,
        text_en=text_en,
        rate_limit_per_second=rate_limit_per_second,
    )
    count = await broadcast_service.enqueue(broadcast)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="create_broadcast",
        entity_type="broadcast",
        entity_id=str(broadcast.id),
        after={"target": target, "recipients": count},
    )
    await session.commit()
    return RedirectResponse(url="/admin/broadcasts", status_code=302)


@router.post("/{broadcast_id}/cancel")
async def cancel_broadcast(
    broadcast_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    broadcast = await uow.broadcasts.get(broadcast_id)
    if broadcast is not None:
        await BroadcastService(uow).cancel(broadcast)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="cancel_broadcast",
            entity_type="broadcast",
            entity_id=str(broadcast_id),
        )
        await session.commit()
    return RedirectResponse(url="/admin/broadcasts", status_code=302)
