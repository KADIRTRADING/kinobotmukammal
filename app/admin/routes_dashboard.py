from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin
from app.admin.templates import templates
from app.config import get_settings
from app.db.models.admin import Admin
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.payments.registry import PaymentRegistry
from app.services.moderation_service import ModerationService
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/admin", tags=["admin-dashboard"])
settings = get_settings()


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    stats = await StatisticsService(uow).dashboard_summary()
    moderation_service = ModerationService(uow)
    moderation = {
        "suspicious_referrals": len(await moderation_service.suspicious_referrals()),
        "pending_promo_links": len(await moderation_service.pending_promo_links()),
        "pending_blogger_applications": len(
            await moderation_service.pending_blogger_applications()
        ),
        "open_support_tickets": len(await moderation_service.open_support_tickets()),
    }
    registry = PaymentRegistry(settings)
    providers = registry.status_report()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "admin": admin,
            "stats": stats,
            "moderation": moderation,
            "providers": providers,
        },
    )


@router.get("/")
async def admin_root():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/admin/dashboard")
