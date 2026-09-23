"""Payment orders admin: browse recent orders, provider status, and issue
refunds through the shared PurchaseService (never a raw status flip)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.config import get_settings
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.payments.registry import PaymentRegistry
from app.services.purchase_service import PurchaseService

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"])
settings = get_settings()


@router.get("", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    orders = await uow.orders.list_recent(limit=100)
    registry = PaymentRegistry(settings)
    providers = registry.status_report()
    return templates.TemplateResponse(
        "orders.html", {"request": request, "orders": orders, "providers": providers}
    )


@router.post("/{order_id}/refund")
async def refund_order(
    order_id: int,
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    order = await uow.orders.get(order_id)
    if order is not None:
        purchase_service = PurchaseService(uow)
        await purchase_service.refund_order(order, reason=reason)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="refund_order",
            entity_type="order",
            entity_id=str(order_id),
            note=reason,
        )
        await session.commit()
    return RedirectResponse(url="/admin/orders", status_code=302)
