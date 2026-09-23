"""Read-only audit log viewer."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin/audit", tags=["admin-audit"])


@router.get("", response_class=HTMLResponse)
async def audit_log(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    logs = await uow.audit.list_recent(limit=200)
    return templates.TemplateResponse("audit.html", {"request": request, "logs": logs})
