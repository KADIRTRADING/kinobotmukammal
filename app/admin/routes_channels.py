"""Mandatory subscription channels management + membership diagnostics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.catalog import MandatoryChannel
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin/channels", tags=["admin-channels"])


@router.get("", response_class=HTMLResponse)
async def list_channels(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    channels = await uow.catalog.list_all_channels()
    return templates.TemplateResponse("channels.html", {"request": request, "channels": channels})


@router.post("/create")
async def create_channel(
    chat_id: str = Form(...),
    title: str = Form(...),
    invite_link: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    channel = MandatoryChannel(chat_id=chat_id, title=title, invite_link=invite_link or None)
    session.add(channel)
    await session.commit()
    return RedirectResponse(url="/admin/channels", status_code=302)


@router.post("/{channel_id}/diagnose")
async def diagnose_channel(
    channel_id: int,
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """Checks that the bot itself is an admin of the channel (required for
    both membership checks and, when relevant, promo attribution-link
    verification of a channel)."""
    uow = UnitOfWork(session)
    channel = await _get_channel(uow, channel_id)
    bot = request.app.state.bot
    is_admin = False
    error = None
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id=channel.chat_id, user_id=me.id)
        is_admin = member.status in ("administrator", "creator")
    except Exception as exc:
        error = str(exc)

    channel.bot_is_admin_verified = is_admin
    await session.commit()
    channels = await uow.catalog.list_all_channels()
    return templates.TemplateResponse(
        "channels.html", {"request": request, "channels": channels, "diagnostic_error": error}
    )


async def _get_channel(uow: UnitOfWork, channel_id: int) -> MandatoryChannel:
    channels = await uow.catalog.list_all_channels()
    for c in channels:
        if c.id == channel_id:
            return c
    raise ValueError("Channel not found")
