"""User search, block/unblock, and balance/premium gifts + manual adjustments."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole, WalletEntryType
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.services.gift_service import GiftService
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_class=HTMLResponse)
async def list_users(
    request: Request,
    q: str = Query(""),
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    users = (
        await uow.users.search_by_name_or_id(q)
        if q
        else await uow.users.search_by_name_or_id("", limit=50)
    )
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "q": q})


@router.post("/{user_id}/block")
async def block_user(
    user_id: int,
    reason: str = Form(""),
    admin: Admin = Depends(
        require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.MODERATOR)
    ),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    user = await uow.users.get_by_id(user_id)
    if user:
        await uow.users.set_blocked(user, True, reason)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="block_user",
            entity_type="user",
            entity_id=str(user_id),
            note=reason,
        )
        await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/{user_id}/unblock")
async def unblock_user(
    user_id: int,
    admin: Admin = Depends(
        require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.MODERATOR)
    ),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    user = await uow.users.get_by_id(user_id)
    if user:
        await uow.users.set_blocked(user, False)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="unblock_user",
            entity_type="user",
            entity_id=str(user_id),
        )
        await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/{user_id}/gift_balance")
async def gift_balance(
    user_id: int,
    amount: int = Form(...),
    currency: str = Form("UZS"),
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    gift_service = GiftService(uow)
    await gift_service.admin_gift_balance(
        admin_id=admin.id,
        recipient_user_id=user_id,
        currency=currency,
        amount=amount,
        reason=reason,
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="gift_balance",
        entity_type="user",
        entity_id=str(user_id),
        after={"amount": amount, "currency": currency},
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/{user_id}/gift_premium")
async def gift_premium(
    user_id: int,
    plan_id: int = Form(...),
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    gift_service = GiftService(uow)
    await gift_service.admin_gift_premium(
        admin_id=admin.id, recipient_user_id=user_id, plan_id=plan_id, reason=reason
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="gift_premium",
        entity_type="user",
        entity_id=str(user_id),
        after={"plan_id": plan_id},
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)


@router.post("/{user_id}/adjust_balance")
async def adjust_balance(
    user_id: int,
    amount: int = Form(...),
    currency: str = Form("UZS"),
    reason: str = Form(...),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN)),
    session: AsyncSession = Depends(get_session),
):
    """Manual admin adjustment; `amount` may be negative to debit. Always
    goes through the locked ledger entry path, never a raw UPDATE."""
    uow = UnitOfWork(session)
    wallet_service = WalletService(uow)
    idempotency_key = f"admin_adjust:{admin.id}:{user_id}:{time.time()}"
    if amount >= 0:
        await wallet_service.credit_available(
            user_id=user_id,
            currency=currency,
            amount=amount,
            entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
            idempotency_key=idempotency_key,
            note=reason,
        )
    else:
        await wallet_service.debit_available(
            user_id=user_id,
            currency=currency,
            amount=-amount,
            entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
            idempotency_key=idempotency_key,
            note=reason,
        )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="adjust_balance",
        entity_type="user",
        entity_id=str(user_id),
        after={"amount": amount, "currency": currency},
        note=reason,
    )
    await session.commit()
    return RedirectResponse(url="/admin/users", status_code=302)
