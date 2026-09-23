"""Premium plans admin: create/edit plans and their PER-PLAN referral
commission percentages, blogger acquisition-reward toggle, and promo
eligibility caps (spec section 3)."""

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

router = APIRouter(prefix="/admin/plans", tags=["admin-plans"])


@router.get("", response_class=HTMLResponse)
async def list_plans(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    plans = await uow.plans.list_all()
    return templates.TemplateResponse("plans.html", {"request": request, "plans": plans})


@router.post("/create")
async def create_plan(
    code: str = Form(...),
    title_uz: str = Form(...),
    title_ru: str = Form(...),
    title_en: str = Form(...),
    duration_days: int = Form(...),
    price_amount: int = Form(...),
    currency: str = Form("UZS"),
    standard_referral_percent: int = Form(0),
    blogger_referral_percent: int = Form(0),
    blogger_acquisition_reward_enabled: bool = Form(True),
    max_discount_percent: int = Form(100),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    plan = await uow.plans.create(
        code=code,
        title_uz=title_uz,
        title_ru=title_ru,
        title_en=title_en,
        duration_days=duration_days,
        price_amount=price_amount,
        currency=currency,
        standard_referral_percent=standard_referral_percent,
        blogger_referral_percent=blogger_referral_percent,
        blogger_acquisition_reward_enabled=blogger_acquisition_reward_enabled,
        max_discount_percent=max_discount_percent,
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="create_plan",
        entity_type="premium_plan",
        entity_id=str(plan.id),
        after={"code": code, "price_amount": price_amount},
    )
    await session.commit()
    return RedirectResponse(url="/admin/plans", status_code=302)


@router.post("/{plan_id}/update")
async def update_plan(
    plan_id: int,
    price_amount: int = Form(...),
    standard_referral_percent: int = Form(...),
    blogger_referral_percent: int = Form(...),
    blogger_acquisition_reward_enabled: bool = Form(True),
    is_active: bool = Form(True),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """Updates only apply going forward: existing Orders/ReferralCommissions
    keep their own frozen snapshot columns, so past purchases are never
    retroactively altered (spec section 3)."""
    uow = UnitOfWork(session)
    plan = await uow.plans.get(plan_id)
    if plan is None:
        return RedirectResponse(url="/admin/plans", status_code=302)
    before = {
        "price_amount": plan.price_amount,
        "standard_referral_percent": plan.standard_referral_percent,
        "blogger_referral_percent": plan.blogger_referral_percent,
    }
    await uow.plans.update(
        plan,
        price_amount=price_amount,
        standard_referral_percent=standard_referral_percent,
        blogger_referral_percent=blogger_referral_percent,
        blogger_acquisition_reward_enabled=blogger_acquisition_reward_enabled,
        is_active=is_active,
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="update_plan",
        entity_type="premium_plan",
        entity_id=str(plan_id),
        before=before,
        after={
            "price_amount": price_amount,
            "standard_referral_percent": standard_referral_percent,
            "blogger_referral_percent": blogger_referral_percent,
        },
    )
    await session.commit()
    return RedirectResponse(url="/admin/plans", status_code=302)
