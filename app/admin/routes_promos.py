"""Admin promo code management: bot-issued codes, creator-link approval,
cancellations, and refunds of unused reserves."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole, PromoKind
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.promo_service import PromoService

router = APIRouter(prefix="/admin/promos", tags=["admin-promos"])


@router.get("", response_class=HTMLResponse)
async def list_promos(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    pending = await uow.promos.list_pending_moderation()
    plans = await uow.plans.list_active()
    return templates.TemplateResponse(
        "promos.html", {"request": request, "pending": pending, "plans": plans}
    )


@router.post("/create_admin_code")
async def create_admin_code(
    plan_id: int = Form(...),
    kind: str = Form(...),
    discount_percent: int = Form(0),
    activations: int = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    plan = await uow.plans.get(plan_id)
    promo_service = PromoService(uow)
    promo = await promo_service.create_admin_code(
        plan=plan, kind=PromoKind(kind), discount_percent=discount_percent, activations=activations
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="create_admin_promo",
        entity_type="promo_code",
        entity_id=str(promo.id),
        after={"code": promo.code},
    )
    await session.commit()
    return RedirectResponse(url="/admin/promos", status_code=302)


@router.post("/{promo_id}/approve")
async def approve_promo(
    promo_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    promo = await _get_promo(uow, promo_id)
    promo_service = PromoService(uow)
    await promo_service.moderate(promo, approve=True, admin_id=admin.id)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="approve_promo",
        entity_type="promo_code",
        entity_id=str(promo_id),
    )
    await session.commit()
    return RedirectResponse(url="/admin/promos", status_code=302)


@router.post("/{promo_id}/reject")
async def reject_promo(
    promo_id: int,
    reason: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    promo = await _get_promo(uow, promo_id)
    promo_service = PromoService(uow)
    await promo_service.moderate(promo, approve=False, admin_id=admin.id, reason=reason)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="reject_promo",
        entity_type="promo_code",
        entity_id=str(promo_id),
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/promos", status_code=302)


@router.post("/{promo_id}/cancel")
async def cancel_promo(
    promo_id: int,
    reason: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    promo = await _get_promo(uow, promo_id)
    promo_service = PromoService(uow)
    await promo_service.cancel(promo, reason=reason)
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="cancel_promo",
        entity_type="promo_code",
        entity_id=str(promo_id),
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/promos", status_code=302)


async def _get_promo(uow: UnitOfWork, promo_id: int):
    from sqlalchemy import select

    from app.db.models.promo import PromoCode

    result = await uow.session.execute(select(PromoCode).where(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if promo is None:
        raise ValueError("Promo not found")
    return promo
