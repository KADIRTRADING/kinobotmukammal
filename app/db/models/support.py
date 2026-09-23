"""Support tickets and threaded messages."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin
from app.db.models.enums import SupportSenderType, SupportTicketStatus


class SupportTicket(IdMixin, TimestampMixin, Base):
    __tablename__ = "support_tickets"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str | None] = mapped_column(String(256), nullable=True)
    status: Mapped[SupportTicketStatus] = mapped_column(
        String(16), nullable=False, default=SupportTicketStatus.OPEN.value
    )
    assigned_admin_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SupportMessage(IdMixin, Base):
    __tablename__ = "support_messages"

    ticket_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sender_type: Mapped[SupportSenderType] = mapped_column(String(16), nullable=False)
    sender_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_file_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
