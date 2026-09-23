"""Admin authentication: bcrypt password hashing + signed session cookie.

Session cookies are signed (not encrypted) with `itsdangerous`, using
`APP_SECRET_KEY`, and carry only the admin's id + role + issue time so a
tampered cookie fails signature verification rather than silently granting
access. `require_role` is a FastAPI dependency factory used to gate each
admin route by the roles allowed to use it.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole
from app.db.session import get_session
from app.db.uow import UnitOfWork

settings = get_settings()
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_signer = TimestampSigner(settings.APP_SECRET_KEY)


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_session_token(admin_id: int) -> str:
    return _signer.sign(str(admin_id).encode("utf-8")).decode("utf-8")


def read_session_token(token: str, max_age: int) -> int | None:
    try:
        raw = _signer.unsign(token, max_age=max_age)
        return int(raw.decode("utf-8"))
    except (BadSignature, SignatureExpired, ValueError):
        return None


async def get_current_admin(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Admin:
    token = request.cookies.get(settings.ADMIN_SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    admin_id = read_session_token(token, max_age=settings.ADMIN_SESSION_TTL_SECONDS)
    if admin_id is None:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})

    uow = UnitOfWork(session)
    admin = await uow.admins.get_by_id(admin_id)
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return admin


def require_role(*roles: AdminRole):
    async def _dependency(admin: Admin = Depends(get_current_admin)) -> Admin:
        if AdminRole(admin.role) not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role for this action")
        return admin

    return _dependency
