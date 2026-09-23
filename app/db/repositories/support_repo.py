from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import SupportSenderType, SupportTicketStatus
from app.db.models.support import SupportMessage, SupportTicket


class SupportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_ticket(self, *, user_id: int, subject: str | None = None) -> SupportTicket:
        ticket = SupportTicket(
            user_id=user_id, subject=subject, status=SupportTicketStatus.OPEN.value
        )
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def get_open_ticket_for_user(self, user_id: int) -> SupportTicket | None:
        stmt = select(SupportTicket).where(
            SupportTicket.user_id == user_id,
            SupportTicket.status.in_(
                [SupportTicketStatus.OPEN.value, SupportTicketStatus.PENDING.value]
            ),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_ticket(self, ticket_id: int) -> SupportTicket | None:
        result = await self.session.execute(
            select(SupportTicket).where(SupportTicket.id == ticket_id)
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        *,
        ticket_id: int,
        sender_type: SupportSenderType,
        sender_id: int,
        text: str | None,
        attachment_file_id: str | None = None,
    ) -> SupportMessage:
        message = SupportMessage(
            ticket_id=ticket_id,
            created_at=dt.datetime.now(dt.UTC),
            sender_type=sender_type.value,
            sender_id=sender_id,
            text=text,
            attachment_file_id=attachment_file_id,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def list_messages(self, ticket_id: int, limit: int = 100) -> list[SupportMessage]:
        stmt = (
            select(SupportMessage)
            .where(SupportMessage.ticket_id == ticket_id)
            .order_by(SupportMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_open(self, limit: int = 50) -> list[SupportTicket]:
        stmt = (
            select(SupportTicket)
            .where(
                SupportTicket.status.in_(
                    [SupportTicketStatus.OPEN.value, SupportTicketStatus.PENDING.value]
                )
            )
            .order_by(SupportTicket.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def close_ticket(self, ticket: SupportTicket) -> None:
        ticket.status = SupportTicketStatus.CLOSED.value
        ticket.closed_at = dt.datetime.now(dt.UTC)
        await self.session.flush()
