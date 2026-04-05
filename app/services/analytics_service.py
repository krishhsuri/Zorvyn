"""
Analytics / dashboard service.

Processes aggregation data from the record repository and shapes it
into the response schemas the API layer returns.

Role-scoping:
  - Admins see all users' data
  - Viewers/Analysts see only their own data
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.repositories import record_repo
from app.schemas.dashboard import (
    CategoryBreakdown,
    RecentActivityResponse,
    SummaryResponse,
    TrendPoint,
)
from app.schemas.record import RecordResponse


def _scope_user_id(user: User):
    """Return None (= all users) for admins, else the user's own ID."""
    return None if user.role == UserRole.ADMIN else user.id


async def get_summary(db: AsyncSession, user: User) -> SummaryResponse:
    """Total income, expenses, balance, record count."""
    data = await record_repo.get_summary(db, user_id=_scope_user_id(user))
    return SummaryResponse(**data)


async def get_category_breakdown(
    db: AsyncSession, user: User
) -> list[CategoryBreakdown]:
    """Per-category totals with percentage share."""
    rows = await record_repo.get_by_category(db, user_id=_scope_user_id(user))
    return [CategoryBreakdown(**r) for r in rows]


async def get_trends(
    db: AsyncSession, user: User, period: str = "monthly"
) -> list[TrendPoint]:
    """Income / expense time-series (monthly or weekly)."""
    rows = await record_repo.get_trends(db, period=period, user_id=_scope_user_id(user))
    return [TrendPoint(**r) for r in rows]


async def get_recent_activity(
    db: AsyncSession, user: User, limit: int = 10
) -> RecentActivityResponse:
    """Most recent N records."""
    records = await record_repo.get_recent(db, limit=limit, user_id=_scope_user_id(user))
    return RecentActivityResponse(
        records=[RecordResponse.model_validate(r) for r in records]
    )
