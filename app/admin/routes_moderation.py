"""Moderation review queue: suspicious referrals and open support tickets
in one place (blogger apps and promo links have their own dedicated pages
but are also summarized here)."""

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
from app.services.moderation_service import ModerationService

router = APIRouter(prefix="/admin/moderation", tags=["admin-moderation"])


@router.get("", response_class=HTMLResponse)
async def moderation_queue(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    moderation_service = ModerationService(uow)
    suspicious_referrals = await moderation_service.suspicious_referrals()
    open_tickets = await moderation_service.open_support_tickets()
    return templates.TemplateResponse(
        "moderation.html",
        {
            "request": request,
            "suspicious_referrals": suspicious_referrals,
            "open_tickets": open_tickets,
        },
    )


@router.post("/tickets/{ticket_id}/reply")
async def reply_ticket(
    ticket_id: int,
    text: str = Form(...),
    request: Request = None,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
):
    from app.db.models.enums import SupportSenderType
    from app.i18n import t

    uow = UnitOfWork(session)
    ticket = await uow.support.get_ticket(ticket_id)
    if ticket is not None:
        await uow.support.add_message(
            ticket_id=ticket_id, sender_type=SupportSenderType.ADMIN, sender_id=admin.id, text=text
        )
        user = await uow.users.get_by_id(ticket.user_id)
        if user is not None:
            try:
                await request.app.state.bot.send_message(
                    chat_id=user.telegram_id,
                    text=t(user.language, "support_ticket_reply_notice", text=text),
                )
            except Exception:
                pass
        await session.commit()
    return RedirectResponse(url="/admin/moderation", status_code=302)


@router.post("/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.SUPPORT)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    ticket = await uow.support.get_ticket(ticket_id)
    if ticket is not None:
        await uow.support.close_ticket(ticket)
        await session.commit()
    return RedirectResponse(url="/admin/moderation", status_code=302)
