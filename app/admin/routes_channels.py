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


def _normalize_chat_id(raw: str) -> str:
    s = raw.strip()
    if s.startswith("https://t.me/"):
        rest = s[len("https://t.me/") :]
        if not rest.startswith(("+", "joinchat/")):
            return f"@{rest.split('/')[0]}"
    return s


@router.post("/create")
async def create_channel(
    request: Request,
    chat_id: str = Form(...),
    title: str = Form(...),
    invite_link: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    norm_chat_id = _normalize_chat_id(chat_id)
    inv = invite_link.strip() or None
    if not inv and chat_id.strip().startswith("https://t.me/"):
        inv = chat_id.strip()

    is_admin = False
    bot = getattr(request.app.state, "bot", None)
    if bot:
        try:
            cid = (
                int(norm_chat_id)
                if (norm_chat_id.startswith("-") or norm_chat_id.isdigit())
                else norm_chat_id
            )
            me = await bot.get_me()
            member = await bot.get_chat_member(chat_id=cid, user_id=me.id)
            is_admin = member.status in ("administrator", "creator")
            if is_admin and not inv:
                try:
                    link_obj = await bot.create_chat_invite_link(chat_id=cid)
                    inv = link_obj.invite_link
                except Exception:
                    try:
                        inv = await bot.export_chat_invite_link(chat_id=cid)
                    except Exception:
                        pass
        except Exception:
            pass

    channel = MandatoryChannel(
        chat_id=norm_chat_id,
        title=title.strip(),
        invite_link=inv,
        is_active=True,
        bot_is_admin_verified=is_admin,
    )
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
    verification of a channel). Also auto-generates invite link if missing."""
    uow = UnitOfWork(session)
    channel = await _get_channel(uow, channel_id)
    bot = getattr(request.app.state, "bot", None)
    is_admin = False
    error = None
    if bot:
        try:
            cid = (
                int(channel.chat_id)
                if (channel.chat_id.startswith("-") or channel.chat_id.isdigit())
                else channel.chat_id
            )
            me = await bot.get_me()
            member = await bot.get_chat_member(chat_id=cid, user_id=me.id)
            is_admin = member.status in ("administrator", "creator")
            if is_admin and (not channel.invite_link or channel.invite_link.startswith("https://t.me/-")):
                try:
                    link_obj = await bot.create_chat_invite_link(chat_id=cid)
                    channel.invite_link = link_obj.invite_link
                except Exception:
                    try:
                        channel.invite_link = await bot.export_chat_invite_link(chat_id=cid)
                    except Exception:
                        pass
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
