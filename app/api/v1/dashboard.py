"""
Dashboard / analytics routes.

All endpoints are read-only and role-scoped:
  - Viewer : summary + recent
  - Analyst : summary + recent + category breakdown + trends
  - Admin  : everything (all users' data)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    CategoryBreakdown,
    RecentActivityResponse,
    SummaryResponse,
    TrendPoint,
)
from app.services import analytics_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])


@router.get("/summary", response_model=SummaryResponse)
async def summary(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Total income, expenses, balance, and record count."""
    return await analytics_service.get_summary(db, user)


@router.get("/by-category", response_model=list[CategoryBreakdown])
async def by_category(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
):
    """Category-wise breakdown with percentage share (analyst + admin)."""
    return await analytics_service.get_category_breakdown(db, user)


@router.get("/trends", response_model=list[TrendPoint])
async def trends(
    period: str = Query("monthly", regex="^(monthly|weekly)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
):
    """Income/expense time-series grouped by month or week (analyst + admin)."""
    return await analytics_service.get_trends(db, user, period=period)


@router.get("/recent", response_model=RecentActivityResponse)
async def recent(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Most recent N financial records."""
    return await analytics_service.get_recent_activity(db, user, limit=limit)
