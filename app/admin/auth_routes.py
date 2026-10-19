"""Admin login/logout routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import create_session_token, read_session_token, verify_password
from app.admin.templates import templates
from app.config import get_settings
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin", tags=["admin-auth"])
settings = get_settings()


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    admin = await uow.admins.get_by_username(username)
    if admin is None or not admin.is_active or not verify_password(password, admin.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=401,
        )

    await uow.admins.touch_login(admin)
    await session.commit()

    token = create_session_token(admin.id)
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    is_secure = request.url.scheme == "https" or settings.is_production
    response.set_cookie(
        key=settings.ADMIN_SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.ADMIN_SESSION_TTL_SECONDS,
        httponly=True,
        samesite="none" if is_secure else "lax",
        secure=is_secure,
    )
    return response


@router.get("/auth/telegram")
async def telegram_auth(
    request: Request,
    token: str,
    session: AsyncSession = Depends(get_session),
):
    """Seamless one-click login for Telegram admins via Mini App or direct link."""
    admin_id = read_session_token(token, max_age=900)
    if admin_id is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Avtorizatsiya havolasi muddati o'tgan yoki yaroqsiz."},
            status_code=401,
        )

    uow = UnitOfWork(session)
    admin = await uow.admins.get_by_id(admin_id)
    if admin is None or not admin.is_active:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Admin hisobi topilmadi yoki faol emas."},
            status_code=401,
        )

    await uow.admins.touch_login(admin)
    await session.commit()

    session_token = create_session_token(admin.id)
    response = RedirectResponse(url="/admin/dashboard", status_code=302)
    is_secure = request.url.scheme == "https" or settings.is_production
    response.set_cookie(
        key=settings.ADMIN_SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.ADMIN_SESSION_TTL_SECONDS,
        httponly=True,
        samesite="none" if is_secure else "lax",
        secure=is_secure,
    )
    return response


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    response = RedirectResponse(url="/admin/login", status_code=302)
    is_secure = request.url.scheme == "https" or settings.is_production
    response.delete_cookie(
        key=settings.ADMIN_SESSION_COOKIE_NAME,
        samesite="none" if is_secure else "lax",
        secure=is_secure,
    )
    return response
