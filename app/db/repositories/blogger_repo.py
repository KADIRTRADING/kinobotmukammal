from __future__ import annotations

import datetime as dt
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blogger import BloggerApplication, BloggerProfile
from app.db.models.enums import BloggerApplicationStatus, BloggerProfileStatus


def generate_verification_phrase() -> str:
    """A short, hard-to-guess-by-accident phrase the applicant must place in
    their bio, e.g. 'moviebot-verify-7f3a9c21'."""
    return f"moviebot-verify-{secrets.token_hex(4)}"


class BloggerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Applications ------------------------------------------------------------
    async def create_application(
        self, *, applicant_user_id: int, platform_name: str | None = None
    ) -> BloggerApplication:
        app = BloggerApplication(
            applicant_user_id=applicant_user_id,
            verification_phrase=generate_verification_phrase(),
            platform_name=platform_name,
            status=BloggerApplicationStatus.PENDING.value,
        )
        self.session.add(app)
        await self.session.flush()
        return app

    async def get_application(self, application_id: int) -> BloggerApplication | None:
        result = await self.session.execute(
            select(BloggerApplication).where(BloggerApplication.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_application_for_user(self, user_id: int) -> BloggerApplication | None:
        result = await self.session.execute(
            select(BloggerApplication).where(
                BloggerApplication.applicant_user_id == user_id,
                BloggerApplication.status == BloggerApplicationStatus.PENDING.value,
            )
        )
        return result.scalar_one_or_none()

    async def submit_url(self, application: BloggerApplication, url: str) -> None:
        application.submitted_url = url
        await self.session.flush()

    async def list_pending(self, limit: int = 50) -> list[BloggerApplication]:
        stmt = (
            select(BloggerApplication)
            .where(BloggerApplication.status == BloggerApplicationStatus.PENDING.value)
            .order_by(BloggerApplication.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def decide(
        self,
        application: BloggerApplication,
        *,
        approve: bool,
        admin_id: int,
        reason: str | None = None,
    ) -> BloggerApplication:
        application.status = (
            BloggerApplicationStatus.APPROVED.value
            if approve
            else BloggerApplicationStatus.REJECTED.value
        )
        application.reviewed_by_admin_id = admin_id
        application.reviewed_at = dt.datetime.now(dt.UTC)
        application.decision_reason = reason
        await self.session.flush()
        return application

    # --- Profiles ------------------------------------------------------------------
    async def get_profile_by_user(self, user_id: int) -> BloggerProfile | None:
        result = await self.session.execute(
            select(BloggerProfile).where(BloggerProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_profile(self, *, user_id: int, approved_application_id: int) -> BloggerProfile:
        profile = BloggerProfile(
            user_id=user_id,
            approved_application_id=approved_application_id,
            status=BloggerProfileStatus.ACTIVE.value,
            approved_at=dt.datetime.now(dt.UTC),
        )
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def suspend(self, profile: BloggerProfile, reason: str | None = None) -> None:
        profile.status = BloggerProfileStatus.SUSPENDED.value
        profile.suspended_at = dt.datetime.now(dt.UTC)
        profile.suspension_reason = reason
        await self.session.flush()

    async def reactivate(self, profile: BloggerProfile) -> None:
        profile.status = BloggerProfileStatus.ACTIVE.value
        profile.suspended_at = None
        profile.suspension_reason = None
        await self.session.flush()

    async def lock_profile(self, user_id: int) -> BloggerProfile | None:
        """Row-lock a blogger profile before mutating its remainder/counter
        fields (used by the acquisition-reward accrual service)."""
        stmt = select(BloggerProfile).where(BloggerProfile.user_id == user_id).with_for_update()
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100) -> list[BloggerProfile]:
        result = await self.session.execute(select(BloggerProfile).limit(limit))
        return list(result.scalars().all())
