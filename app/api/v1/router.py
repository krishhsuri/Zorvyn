"""
V1 API router — aggregates all sub-routers under /api/v1.

Adding a new feature module is a one-line change here (low coupling).
"""

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, records, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(records.router)
router.include_router(dashboard.router)
