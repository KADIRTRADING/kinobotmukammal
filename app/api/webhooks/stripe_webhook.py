"""Stripe webhook endpoint for the independent web storefront.

Verifies the Stripe-Signature header (see StripeProvider.parse_webhook)
before treating anything as proof of payment, then routes to
`PurchaseService.confirm_payment` / `refund_order` -- the exact same code
path used by the Telegram Stars success handler and the wallet checkout,
so premium is always activated exactly once regardless of which provider
paid for it.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork
from app.payments.base import PaymentEventType
from app.payments.stripe_provider import StripeProvider

router = APIRouter(prefix="/webhooks/stripe", tags=["stripe-webhook"])
settings = get_settings()


@router.post("")
async def stripe_webhook(request: Request) -> Response:
    provider = StripeProvider(settings)
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}

    event = await provider.parse_webhook(headers=headers, body=body)
    if not event.verified:
        return Response(status_code=400, content="invalid signature")

    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        try:
            existing = await uow.orders.get_provider_event("stripe", event.provider_event_id)
            if existing is not None:
                await session.commit()
                return Response(status_code=200)  # duplicate delivery -- already processed

            order = await uow.orders.get_by_uid(event.order_uid) if event.order_uid else None
            await uow.orders.create_provider_event(
                provider_code="stripe",
                provider_event_id=event.provider_event_id,
                event_type=event.event_type.value,
                order_id=order.id if order else None,
                raw_payload=event.raw_payload,
                processed=True,
            )

            if order is not None:
                from app.services.purchase_service import PurchaseService

                purchase_service = PurchaseService(uow)
                if event.event_type == PaymentEventType.PAYMENT_SUCCEEDED:
                    await purchase_service.confirm_payment(
                        order, provider_reference=event.provider_reference
                    )
                elif event.event_type in (PaymentEventType.REFUNDED,):
                    await purchase_service.refund_order(order, reason="stripe_refund_event")
                elif event.event_type == PaymentEventType.DISPUTED:
                    from app.bot.handlers.admin_notifications import notify_admins_payment_problem

                    await notify_admins_payment_problem(
                        request.app.state.bot,
                        uow,
                        order_uid=str(order.uid),
                        reason="stripe_dispute",
                    )

            await session.commit()
        except Exception:
            await session.rollback()
            raise

    return Response(status_code=200)
