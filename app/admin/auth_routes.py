"""Admin login/logout routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import create_session_token, verify_password
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
    response.set_cookie(
        key=settings.ADMIN_SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.ADMIN_SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
    )
    return response


@router.get("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(settings.ADMIN_SESSION_COOKIE_NAME)
    return response
