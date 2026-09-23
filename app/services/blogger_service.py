"""Blogger application/verification workflow (spec section 5).

Verification is HONEST about its limits: `attempt_automated_check` only
ever runs when an authorized platform API is actually configured for the
given platform (currently: none are, see README "What still needs
credentials"). Otherwise every application requires manual admin review --
the service never pretends to have checked an inaccessible bio.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.db.models.blogger import BloggerApplication
from app.db.models.enums import BloggerStatusCache
from app.db.uow import UnitOfWork


@dataclass(frozen=True)
class ApplicationStartResult:
    application: BloggerApplication
    already_pending: bool


class BloggerService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    async def start_application(
        self, *, applicant_user_id: int, platform_name: str | None = None
    ) -> ApplicationStartResult:
        existing = await self.uow.bloggers.get_pending_application_for_user(applicant_user_id)
        if existing is not None:
            return ApplicationStartResult(application=existing, already_pending=True)

        application = await self.uow.bloggers.create_application(
            applicant_user_id=applicant_user_id, platform_name=platform_name
        )
        user = await self.uow.users.get_by_id(applicant_user_id)
        if user is not None:
            user.blogger_status_cache = BloggerStatusCache.PENDING.value
            await self.uow.flush()
        return ApplicationStartResult(application=application, already_pending=False)

    async def submit_url(self, application: BloggerApplication, url: str) -> None:
        await self.uow.bloggers.submit_url(application, url)

    async def attempt_automated_check(self, application: BloggerApplication) -> str | None:
        """Only returns a non-None result for platforms with a real,
        configured, authorized API integration. Today that is NONE, so this
        always returns None and the application proceeds to manual review.
        This function exists (rather than being omitted) so that adding a
        real integration later is a one-place change, and so the admin
        panel can show "automated check: not available for this platform"
        instead of silently doing nothing.
        """
        application.auto_check_attempted = True
        application.auto_check_result = (
            "No authorized platform API is configured for automated bio verification; "
            "manual admin review is required."
        )
        await self.uow.flush()
        return None

    async def decide(
        self,
        application: BloggerApplication,
        *,
        approve: bool,
        admin_id: int,
        reason: str | None = None,
    ) -> BloggerApplication:
        application = await self.uow.bloggers.decide(
            application, approve=approve, admin_id=admin_id, reason=reason
        )
        user = await self.uow.users.get_by_id(application.applicant_user_id)
        if approve:
            await self.uow.bloggers.create_profile(
                user_id=application.applicant_user_id, approved_application_id=application.id
            )
            if user is not None:
                user.blogger_status_cache = BloggerStatusCache.APPROVED.value
        else:
            if user is not None:
                user.blogger_status_cache = BloggerStatusCache.REJECTED.value
        await self.uow.flush()
        return application

    async def suspend(self, blogger_user_id: int, reason: str | None = None) -> bool:
        profile = await self.uow.bloggers.get_profile_by_user(blogger_user_id)
        if profile is None:
            return False
        await self.uow.bloggers.suspend(profile, reason)
        user = await self.uow.users.get_by_id(blogger_user_id)
        if user is not None:
            user.blogger_status_cache = BloggerStatusCache.SUSPENDED.value
            await self.uow.flush()
        return True

    async def reactivate(self, blogger_user_id: int) -> bool:
        profile = await self.uow.bloggers.get_profile_by_user(blogger_user_id)
        if profile is None:
            return False
        await self.uow.bloggers.reactivate(profile)
        user = await self.uow.users.get_by_id(blogger_user_id)
        if user is not None:
            user.blogger_status_cache = BloggerStatusCache.APPROVED.value
            await self.uow.flush()
        return True

    async def is_active_blogger(self, user_id: int) -> bool:
        profile = await self.uow.bloggers.get_profile_by_user(user_id)
        return bool(profile and profile.status == "active")
