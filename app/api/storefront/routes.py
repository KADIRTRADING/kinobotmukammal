"""Storefront checkout routes: list plans, create a Stripe/Click charge,
and simple success/cancel landing pages. Requires the buyer to identify
their Telegram account (telegram_id) so the resulting entitlement can be
linked back to their bot account -- this is a legitimate independent web
purchase flow, not a bot-triggered redirect (see compliance note above).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.enums import PaymentProviderCode
from app.db.session import get_session
from app.db.uow import UnitOfWork
from app.payments.registry import PaymentRegistry
from app.services.purchase_service import PurchaseService

router = APIRouter(prefix="/storefront", tags=["storefront"])
settings = get_settings()


def _require_storefront_enabled() -> None:
    if not settings.STOREFRONT_ENABLED:
        raise HTTPException(status_code=404, detail="Storefront is disabled")


@router.get("/plans")
async def list_plans(session: AsyncSession = Depends(get_session)) -> list[dict]:
    _require_storefront_enabled()
    uow = UnitOfWork(session)
    plans = await uow.plans.list_active()
    return [
        {
            "id": p.id,
            "code": p.code,
            "title": p.title_en,
            "duration_days": p.duration_days,
            "price_amount": p.price_amount,
            "currency": p.currency,
        }
        for p in plans
    ]


@router.post("/checkout")
async def create_checkout(
    plan_id: int,
    provider: str,
    telegram_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    _require_storefront_enabled()
    if provider not in (PaymentProviderCode.STRIPE.value, PaymentProviderCode.CLICK.value):
        raise HTTPException(status_code=400, detail="Unsupported storefront provider")

    uow = UnitOfWork(session)
    plan = await uow.plans.get(plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=404, detail="Plan not found")

    user = await uow.users.get_by_telegram_id(telegram_id)
    if user is None:
        raise HTTPException(
            status_code=400,
            detail="This Telegram account has not started the bot yet. Start the bot first so we can link your purchase.",
        )

    registry = PaymentRegistry(settings)
    try:
        provider_impl = registry.get_enabled(provider)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=user.id, plan=plan, provider_code=PaymentProviderCode(provider)
    )
    charge = await provider_impl.create_charge(
        order_uid=str(order.uid),
        amount=order.net_amount,
        currency=order.currency,
        description=plan.title_en,
        buyer_telegram_id=telegram_id,
    )
    await session.commit()
    return {"order_uid": str(order.uid), **charge.checkout_payload}


@router.get("/success")
async def checkout_success(order: str = Query(...)) -> dict:
    return {
        "status": "received",
        "message": "Payment received; premium will activate once the provider confirms the charge.",
    }


@router.get("/cancel")
async def checkout_cancel(order: str = Query(...)) -> dict:
    return {"status": "cancelled", "order_uid": order}
