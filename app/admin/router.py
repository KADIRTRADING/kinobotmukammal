"""Aggregates every admin sub-router into a single `admin_router` mounted
by `app.main`."""

from __future__ import annotations

from fastapi import APIRouter

from app.admin import (
    auth_routes,
    routes_audit,
    routes_bloggers,
    routes_broadcasts,
    routes_channels,
    routes_dashboard,
    routes_moderation,
    routes_movies,
    routes_orders,
    routes_plans,
    routes_promos,
    routes_users,
)

admin_router = APIRouter()
admin_router.include_router(auth_routes.router)
admin_router.include_router(routes_dashboard.router)
admin_router.include_router(routes_movies.router)
admin_router.include_router(routes_channels.router)
admin_router.include_router(routes_plans.router)
admin_router.include_router(routes_users.router)
admin_router.include_router(routes_promos.router)
admin_router.include_router(routes_bloggers.router)
admin_router.include_router(routes_orders.router)
admin_router.include_router(routes_broadcasts.router)
admin_router.include_router(routes_moderation.router)
admin_router.include_router(routes_audit.router)
