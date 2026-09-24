from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import OrderStatus, PaymentProviderCode
from app.db.models.order import Entitlement, Order, ProviderEvent


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, **kwargs) -> Order:
        order = Order(**kwargs)
        self.session.add(order)
        await self.session.flush()
        return order

    async def get(self, order_id: int) -> Order | None:
        result = await self.session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def get_by_uid(self, uid: UUID | str) -> Order | None:
        result = await self.session.execute(select(Order).where(Order.uid == uid))
        return result.scalar_one_or_none()

    async def lock(self, order_id: int) -> Order | None:
        stmt = select(Order).where(Order.id == order_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_paid(self, order: Order, *, provider_reference: str | None = None) -> Order:
        order.status = OrderStatus.PAID.value
        order.paid_at = dt.datetime.now(dt.UTC)
        if provider_reference:
            order.provider_reference = provider_reference
        await self.session.flush()
        return order

    async def mark_failed(self, order: Order, reason: str) -> Order:
        order.status = OrderStatus.FAILED.value
        order.failure_reason = reason
        await self.session.flush()
        return order

    async def mark_cancelled(self, order: Order, reason: str | None = None) -> Order:
        order.status = OrderStatus.CANCELLED.value
        order.cancelled_at = dt.datetime.now(dt.UTC)
        order.failure_reason = reason
        await self.session.flush()
        return order

    async def mark_refunded(self, order: Order, reason: str | None = None) -> Order:
        order.status = OrderStatus.REFUNDED.value
        order.refunded_at = dt.datetime.now(dt.UTC)
        order.refund_reason = reason
        await self.session.flush()
        return order

    async def list_for_user(self, user_id: int, limit: int = 50, offset: int = 0) -> list[Order]:
        stmt = (
            select(Order)
            .where(Order.buyer_user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: int) -> int:
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(Order.id)).where(Order.buyer_user_id == user_id)
        )
        return int(result.scalar_one())

    async def list_recent(
        self, limit: int = 100, status: str | None = None, offset: int = 0
    ) -> list[Order]:
        stmt = select(Order).order_by(Order.created_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Order.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_recent(self, status: str | None = None) -> int:
        from sqlalchemy import func

        stmt = select(func.count(Order.id))
        if status:
            stmt = stmt.where(Order.status == status)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_provider_events_for_order(
        self, order_id: int, limit: int = 50
    ) -> list[ProviderEvent]:
        stmt = (
            select(ProviderEvent)
            .where(ProviderEvent.order_id == order_id)
            .order_by(ProviderEvent.received_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Provider events (idempotency) --------------------------------------------
    async def get_provider_event(
        self, provider_code: PaymentProviderCode | str, provider_event_id: str
    ) -> ProviderEvent | None:
        code = (
            provider_code.value if isinstance(provider_code, PaymentProviderCode) else provider_code
        )
        result = await self.session.execute(
            select(ProviderEvent).where(
                ProviderEvent.provider_code == code,
                ProviderEvent.provider_event_id == provider_event_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_provider_event(self, **kwargs) -> ProviderEvent:
        event = ProviderEvent(received_at=dt.datetime.now(dt.UTC), **kwargs)
        self.session.add(event)
        await self.session.flush()
        return event

    async def mark_event_processed(self, event: ProviderEvent, error: str | None = None) -> None:
        event.processed = error is None
        event.processing_error = error
        await self.session.flush()

    # --- Entitlements ----------------------------------------------------------
    async def get_entitlement_by_source(
        self, source: str, source_reference: str
    ) -> Entitlement | None:
        result = await self.session.execute(
            select(Entitlement).where(
                Entitlement.source == source, Entitlement.source_reference == source_reference
            )
        )
        return result.scalar_one_or_none()

    async def create_entitlement(self, **kwargs) -> Entitlement:
        entitlement = Entitlement(**kwargs)
        self.session.add(entitlement)
        await self.session.flush()
        return entitlement

    async def list_entitlements_for_user(self, user_id: int, limit: int = 50) -> list[Entitlement]:
        stmt = (
            select(Entitlement)
            .where(Entitlement.user_id == user_id)
            .order_by(Entitlement.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
