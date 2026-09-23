from __future__ import annotations

import datetime as dt
import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.promo import PromoCode, PromoRedemption

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def generate_promo_code(length: int = 8) -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(length))


class PromoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_code(self, code: str) -> PromoCode | None:
        result = await self.session.execute(select(PromoCode).where(PromoCode.code == code.upper()))
        return result.scalar_one_or_none()

    async def lock_by_code(self, code: str) -> PromoCode | None:
        """Row-lock the promo for atomic redemption. Combined with the
        DB-level CHECK(remaining_uses >= 0) this makes a double-spend on
        the last remaining use structurally impossible even under two
        simultaneous redeemers."""
        stmt = select(PromoCode).where(PromoCode.code == code.upper()).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PromoCode:
        code = kwargs.pop("code", None) or generate_promo_code()
        while await self.get_by_code(code) is not None:
            code = generate_promo_code()
        promo = PromoCode(code=code, **kwargs)
        self.session.add(promo)
        await self.session.flush()
        return promo

    async def decrement_remaining_use(self, promo: PromoCode) -> None:
        if promo.remaining_uses <= 0:
            raise ValueError("Promo code has no remaining uses")
        promo.remaining_uses -= 1
        await self.session.flush()

    async def has_user_redeemed(self, promo_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            select(PromoRedemption).where(
                PromoRedemption.promo_code_id == promo_id,
                PromoRedemption.redeemer_user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_redemption(self, **kwargs) -> PromoRedemption:
        redemption = PromoRedemption(**kwargs)
        self.session.add(redemption)
        await self.session.flush()
        return redemption

    async def list_redemptions(self, promo_id: int, limit: int = 100) -> list[PromoRedemption]:
        stmt = (
            select(PromoRedemption)
            .where(PromoRedemption.promo_code_id == promo_id)
            .order_by(PromoRedemption.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_issuer(self, issuer_user_id: int, limit: int = 50) -> list[PromoCode]:
        stmt = (
            select(PromoCode)
            .where(PromoCode.issuer_user_id == issuer_user_id)
            .order_by(PromoCode.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending_moderation(self, limit: int = 50) -> list[PromoCode]:
        from app.db.models.enums import PromoModerationStatus

        stmt = (
            select(PromoCode)
            .where(PromoCode.moderation_status == PromoModerationStatus.PENDING.value)
            .order_by(PromoCode.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_expired_unreleased(self, limit: int = 200) -> list[PromoCode]:
        now = dt.datetime.now(dt.UTC)
        stmt = (
            select(PromoCode)
            .where(
                PromoCode.is_active.is_(True),
                PromoCode.is_funds_released.is_(False),
                PromoCode.expires_at.is_not(None),
                PromoCode.expires_at <= now,
            )
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def cancel(self, promo: PromoCode, reason: str | None = None) -> None:
        promo.is_active = False
        promo.cancelled_at = dt.datetime.now(dt.UTC)
        promo.cancelled_reason = reason
        await self.session.flush()

    async def mark_funds_released(self, promo: PromoCode) -> None:
        promo.is_funds_released = True
        await self.session.flush()
