"""Integration tests: admin panel "Orders/payments" section -- the critical
safety invariant that `PurchaseService.refund_order` (the ONLY mutation
`app/bot/handlers/admin/orders.py` ever calls) can only act on an
already-PAID order, and can NEVER be used to mark a PENDING order as paid.
`PurchaseService.confirm_payment` -- the only method that ever sets
status=PAID -- is intentionally never imported by the admin orders
handler; these tests exercise the service-level guarantee directly."""

from __future__ import annotations

import pytest

from app.db.models.enums import OrderStatus, PaymentProviderCode
from app.services.purchase_service import PurchaseService


@pytest.mark.asyncio
async def test_refund_order_is_a_no_op_on_a_pending_order(uow, make_user, make_plan):
    buyer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    assert order.status == OrderStatus.PENDING.value

    # The critical invariant: calling refund_order on a never-paid order
    # must NOT transition it to PAID (or to REFUNDED) -- it does nothing.
    await purchase_service.refund_order(order, reason="admin misclick")

    refreshed = await uow.orders.get(order.id)
    assert refreshed.status == OrderStatus.PENDING.value
    assert refreshed.status != OrderStatus.PAID.value

    buyer_refreshed = await uow.users.get_by_id(buyer.id)
    assert buyer_refreshed.premium_until is None


@pytest.mark.asyncio
async def test_refund_order_succeeds_only_after_payment_confirmed(uow, make_user, make_plan):
    buyer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS", duration_days=30)
    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order)

    order_paid = await uow.orders.get(order.id)
    assert order_paid.status == OrderStatus.PAID.value

    await purchase_service.refund_order(order_paid, reason="buyer requested cancellation")

    refreshed = await uow.orders.get(order.id)
    assert refreshed.status == OrderStatus.REFUNDED.value

    buyer_refreshed = await uow.users.get_by_id(buyer.id)
    import datetime as dt

    assert buyer_refreshed.premium_until <= dt.datetime.now(dt.UTC) + dt.timedelta(seconds=5)


@pytest.mark.asyncio
async def test_refund_order_is_idempotent_and_never_double_refunds(uow, make_user, make_plan):
    buyer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await purchase_service.confirm_payment(order)
    order_paid = await uow.orders.get(order.id)

    await purchase_service.refund_order(order_paid, reason="first refund")
    refunded_once = await uow.orders.get(order.id)
    first_refunded_at = refunded_once.refunded_at
    assert refunded_once.status == OrderStatus.REFUNDED.value

    # A second refund attempt on an already-refunded order must be a no-op.
    await purchase_service.refund_order(refunded_once, reason="duplicate admin click")
    refunded_twice = await uow.orders.get(order.id)
    assert refunded_twice.refunded_at == first_refunded_at


@pytest.mark.asyncio
async def test_no_admin_code_path_ever_imports_confirm_payment():
    """Static safety check mirrored from this session's cross-reference
    verification: `app/bot/handlers/admin/orders.py` must never import or
    call `PurchaseService.confirm_payment` -- the only method that can ever
    set an order's status to PAID. This protects the spec requirement:
    "never mark an order paid via button"."""
    import ast
    from pathlib import Path

    orders_handler_path = (
        Path(__file__).resolve().parents[2] / "app" / "bot" / "handlers" / "admin" / "orders.py"
    )
    source = orders_handler_path.read_text()
    tree = ast.parse(source)

    called_attrs = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "confirm_payment" not in called_attrs
    assert "mark_paid" not in called_attrs


@pytest.mark.asyncio
async def test_provider_events_are_listed_for_an_order_without_mutating_it(
    uow, make_user, make_plan
):
    buyer = await make_user()
    plan = await make_plan(price_amount=5000, currency="UZS")
    purchase_service = PurchaseService(uow)
    order = await purchase_service.create_order(
        buyer_user_id=buyer.id, plan=plan, provider_code=PaymentProviderCode.WALLET
    )
    await uow.orders.create_provider_event(
        order_id=order.id,
        provider_code=PaymentProviderCode.WALLET.value,
        provider_event_id="evt_1",
        event_type="charge.succeeded",
        raw_payload={"raw": "data"},
        processed=True,
    )

    events = await uow.orders.list_provider_events_for_order(order.id)
    assert len(events) == 1
    assert events[0].provider_event_id == "evt_1"

    unchanged = await uow.orders.get(order.id)
    assert unchanged.status == OrderStatus.PENDING.value
