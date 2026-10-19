"""Movies, categories, and mandatory-channel admin management.

Video upload: admins forward/send a video message to the BOT (not to this
web panel -- Telegram video uploads only make sense through Telegram
itself), and the bot's admin-only handler (see
app.bot.handlers.movies -- MovieAdminStates flow, wired for users whose
telegram_id is registered as an Admin) captures the resulting `file_id`
and calls the same `CatalogRepository.create` used here. This web panel
covers metadata editing, publishing state, and category assignment, which
don't require a live Telegram upload.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.security import get_current_admin, require_role
from app.admin.templates import templates
from app.db.models.admin import Admin
from app.db.models.enums import AdminRole, MoviePublicationState
from app.db.session import get_session
from app.db.uow import UnitOfWork

router = APIRouter(prefix="/admin/movies", tags=["admin-movies"])


@router.get("", response_class=HTMLResponse)
async def list_movies(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    uow = UnitOfWork(session)
    categories = await uow.catalog.list_active_categories()
    movies = await uow.catalog.list_all_movies()
    return templates.TemplateResponse(
        "movies.html", {"request": request, "movies": movies, "categories": categories}
    )


@router.post("/create")
async def create_movie(
    request: Request,
    code: str = Form(...),
    title_uz: str = Form(...),
    title_ru: str = Form(""),
    title_en: str = Form(""),
    video_file_id: str = Form(...),
    access_type: str = Form("free"),
    category_id: str = Form(""),
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    cid = int(category_id) if category_id and category_id.isdigit() else None
    movie = await uow.catalog.create(
        code=code.strip(),
        title_uz=title_uz.strip(),
        title_ru=title_ru.strip() or title_uz.strip(),
        title_en=title_en.strip() or title_uz.strip(),
        video_file_id=video_file_id.strip(),
        category_id=cid,
        access_type=access_type,
        publication_state=MoviePublicationState.PUBLISHED.value,
    )
    await uow.audit.record(
        admin_id=admin.id,
        admin_username=admin.username,
        action="create_movie",
        entity_type="movie",
        entity_id=str(movie.id),
        after={"code": movie.code, "title_uz": movie.title_uz},
    )
    await session.commit()
    return RedirectResponse(url="/admin/movies", status_code=302)


@router.post("/{movie_id}/publish")
async def publish_movie(
    movie_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    movie = await uow.catalog.get_by_id(movie_id)
    if movie:
        before = {"publication_state": movie.publication_state}
        await uow.catalog.update(movie, publication_state=MoviePublicationState.PUBLISHED.value)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="publish_movie",
            entity_type="movie",
            entity_id=str(movie_id),
            before=before,
            after={"publication_state": "published"},
        )
        await session.commit()
    return RedirectResponse(url="/admin/movies", status_code=302)


@router.post("/{movie_id}/archive")
async def archive_movie(
    movie_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    movie = await uow.catalog.get_by_id(movie_id)
    if movie:
        before = {"publication_state": movie.publication_state}
        await uow.catalog.update(movie, publication_state=MoviePublicationState.ARCHIVED.value)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="archive_movie",
            entity_type="movie",
            entity_id=str(movie_id),
            before=before,
            after={"publication_state": "archived"},
        )
        await session.commit()
    return RedirectResponse(url="/admin/movies", status_code=302)


@router.post("/{movie_id}/delete")
async def delete_movie(
    movie_id: int,
    admin: Admin = Depends(require_role(AdminRole.SUPERADMIN)),
    session: AsyncSession = Depends(get_session),
):
    uow = UnitOfWork(session)
    movie = await uow.catalog.get_by_id(movie_id)
    if movie:
        await session.delete(movie)
        await uow.audit.record(
            admin_id=admin.id,
            admin_username=admin.username,
            action="delete_movie",
            entity_type="movie",
            entity_id=str(movie_id),
        )
        await session.commit()
    return RedirectResponse(url="/admin/movies", status_code=302)
