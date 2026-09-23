"""Click (click.uz) merchant webhook endpoint for the independent web
storefront: implements the two-step Prepare (action=0) / Complete
(action=1) protocol per Click's Shop API, responding with the exact JSON
shape Click's merchant integration expects on each step.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Request, Response

from app.config import get_settings
from app.db.session import AsyncSessionLocal
from app.db.uow import UnitOfWork
from app.payments.click_provider import ClickActionCode, ClickErrorCode, ClickProvider

router = APIRouter(prefix="/webhooks/click", tags=["click-webhook"])
settings = get_settings()


@router.post("")
async def click_webhook(request: Request) -> Response:
    form = await request.form()
    data = dict(form)
    provider = ClickProvider(settings)
    event = await provider.parse_webhook(headers={}, body=json.dumps(data).encode("utf-8"))

    if not event.verified:
        return _json_response(
            {"error": ClickErrorCode.SIGN_CHECK_FAILED, "error_note": "SIGN CHECK FAILED"}
        )

    async with AsyncSessionLocal() as session:
        uow = UnitOfWork(session)
        try:
            order = await uow.orders.get_by_uid(event.order_uid) if event.order_uid else None
            if order is None:
                await session.commit()
                return _json_response(
                    {"error": ClickErrorCode.TRANSACTION_NOT_FOUND, "error_note": "Order not found"}
                )

            action = str(data.get("action"))
            existing = await uow.orders.get_provider_event(
                "click", f"{event.provider_event_id}:{action}"
            )
            if existing is not None:
                await session.commit()
                return _json_response(
                    {
                        "click_trans_id": data.get("click_trans_id"),
                        "merchant_trans_id": data.get("merchant_trans_id"),
                        (
                            "merchant_prepare_id"
                            if action == str(ClickActionCode.PREPARE)
                            else "merchant_confirm_id"
                        ): order.id,
                        "error": ClickErrorCode.SUCCESS,
                        "error_note": "Already processed",
                    }
                )

            await uow.orders.create_provider_event(
                provider_code="click",
                provider_event_id=f"{event.provider_event_id}:{action}",
                event_type=f"click_action_{action}",
                order_id=order.id,
                raw_payload=data,
                processed=True,
            )

            if action == str(ClickActionCode.PREPARE):
                await session.commit()
                return _json_response(
                    {
                        "click_trans_id": data.get("click_trans_id"),
                        "merchant_trans_id": data.get("merchant_trans_id"),
                        "merchant_prepare_id": order.id,
                        "error": ClickErrorCode.SUCCESS,
                        "error_note": "Success",
                    }
                )

            # Complete step: activate premium via the shared purchase service.
            from app.services.purchase_service import PurchaseService

            purchase_service = PurchaseService(uow)
            await purchase_service.confirm_payment(
                order, provider_reference=event.provider_reference
            )
            await session.commit()
            return _json_response(
                {
                    "click_trans_id": data.get("click_trans_id"),
                    "merchant_trans_id": data.get("merchant_trans_id"),
                    "merchant_confirm_id": order.id,
                    "error": ClickErrorCode.SUCCESS,
                    "error_note": "Success",
                }
            )
        except Exception:
            await session.rollback()
            raise


def _json_response(payload: dict) -> Response:
    return Response(content=json.dumps(payload), media_type="application/json")
