"""
Repository for FinancialRecord database operations.

Handles CRUD, filtered listing, and raw aggregation queries that the
analytics service layer consumes.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import FinancialRecord, RecordType


# ── CRUD ──────────────────────────────────────────────────────────────────────


async def create_record(db: AsyncSession, **kwargs) -> FinancialRecord:
    record = FinancialRecord(**kwargs)
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_record(db: AsyncSession, record_id: uuid.UUID) -> FinancialRecord | None:
    stmt = select(FinancialRecord).where(
        FinancialRecord.id == record_id,
        FinancialRecord.is_deleted == False,  # noqa: E712
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_record(
    db: AsyncSession, record: FinancialRecord, **kwargs
) -> FinancialRecord:
    for key, value in kwargs.items():
        if value is not None:
            setattr(record, key, value)
    await db.flush()
    await db.refresh(record)
    return record


async def soft_delete(db: AsyncSession, record: FinancialRecord) -> FinancialRecord:
    record.is_deleted = True
    await db.flush()
    await db.refresh(record)
    return record


# ── Filtered Listing ──────────────────────────────────────────────────────────


async def list_records(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    record_type: RecordType | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[FinancialRecord], int]:
    """Return filtered, paginated records and total count."""

    base = select(FinancialRecord).where(FinancialRecord.is_deleted == False)  # noqa: E712

    if user_id is not None:
        base = base.where(FinancialRecord.user_id == user_id)
    if record_type is not None:
        base = base.where(FinancialRecord.type == record_type)
    if category is not None:
        base = base.where(FinancialRecord.category == category.lower())
    if date_from is not None:
        base = base.where(FinancialRecord.date >= date_from)
    if date_to is not None:
        base = base.where(FinancialRecord.date <= date_to)
    if search is not None:
        pattern = f"%{search}%"
        base = base.where(
            FinancialRecord.description.ilike(pattern)
            | FinancialRecord.category.ilike(pattern)
        )

    # Total count (reuse the WHERE clause)
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated data
    offset = (page - 1) * limit
    data_stmt = base.order_by(FinancialRecord.date.desc()).offset(offset).limit(limit)
    result = await db.execute(data_stmt)

    return list(result.scalars().all()), total


# ── Aggregations ──────────────────────────────────────────────────────────────


async def get_summary(
    db: AsyncSession, user_id: uuid.UUID | None = None
) -> dict:
    """Return total income, total expenses, balance, and count."""
    base = select(
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                    else_=Decimal("0"),
                )
            ),
            Decimal("0"),
        ).label("total_income"),
        func.coalesce(
            func.sum(
                case(
                    (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                    else_=Decimal("0"),
                )
            ),
            Decimal("0"),
        ).label("total_expenses"),
        func.count().label("record_count"),
    ).where(FinancialRecord.is_deleted == False)  # noqa: E712

    if user_id is not None:
        base = base.where(FinancialRecord.user_id == user_id)

    row = (await db.execute(base)).one()

    return {
        "total_income": row.total_income,
        "total_expenses": row.total_expenses,
        "balance": row.total_income - row.total_expenses,
        "record_count": row.record_count,
    }


async def get_by_category(
    db: AsyncSession, user_id: uuid.UUID | None = None
) -> list[dict]:
    """Category-wise breakdown with totals and counts."""
    base = (
        select(
            FinancialRecord.category,
            func.sum(FinancialRecord.amount).label("total"),
            func.count().label("count"),
        )
        .where(FinancialRecord.is_deleted == False)  # noqa: E712
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
    )

    if user_id is not None:
        base = base.where(FinancialRecord.user_id == user_id)

    rows = (await db.execute(base)).all()

    grand_total = sum(r.total for r in rows) or Decimal("1")
    return [
        {
            "category": r.category,
            "total": r.total,
            "count": r.count,
            "percentage": round(float(r.total / grand_total * 100), 2),
        }
        for r in rows
    ]


async def get_trends(
    db: AsyncSession,
    period: str = "monthly",
    user_id: uuid.UUID | None = None,
) -> list[dict]:
    """Income/expense totals grouped by month or week."""
    if period == "weekly":
        # ISO week: YYYY-WNN
        period_expr = func.to_char(FinancialRecord.date, "IYYY-\"W\"IW")
    else:
        period_expr = func.to_char(FinancialRecord.date, "YYYY-MM")

    base = (
        select(
            period_expr.label("period"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.INCOME, FinancialRecord.amount),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("income"),
            func.coalesce(
                func.sum(
                    case(
                        (FinancialRecord.type == RecordType.EXPENSE, FinancialRecord.amount),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("expense"),
        )
        .where(FinancialRecord.is_deleted == False)  # noqa: E712
        .group_by(period_expr)
        .order_by(period_expr)
    )

    if user_id is not None:
        base = base.where(FinancialRecord.user_id == user_id)

    rows = (await db.execute(base)).all()
    return [
        {
            "period": r.period,
            "income": r.income,
            "expense": r.expense,
            "balance": r.income - r.expense,
        }
        for r in rows
    ]


async def get_recent(
    db: AsyncSession,
    limit: int = 10,
    user_id: uuid.UUID | None = None,
) -> list[FinancialRecord]:
    """Most recent N non-deleted records."""
    stmt = (
        select(FinancialRecord)
        .where(FinancialRecord.is_deleted == False)  # noqa: E712
        .order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
        .limit(limit)
    )
    if user_id is not None:
        stmt = stmt.where(FinancialRecord.user_id == user_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())
