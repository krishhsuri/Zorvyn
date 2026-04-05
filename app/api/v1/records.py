"""
Financial record routes — CRUD with filtering, pagination, and export.

Role-based access:
  - Viewer  : GET (own records only)
  - Analyst : GET + filters + export (own records only)
  - Admin   : Full CRUD on all records
"""

import csv
import io
import json
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.database import get_db
from app.models.record import RecordType
from app.models.user import User, UserRole
from app.schemas.record import (
    PaginatedResponse,
    RecordCreate,
    RecordFilter,
    RecordResponse,
    RecordUpdate,
)
from app.services import record_service

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.post(
    "/",
    response_model=RecordResponse,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def create_record(
    body: RecordCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Create a new financial record (admin only)."""
    return await record_service.create_record(db, user, body)


@router.get("/", response_model=PaginatedResponse[RecordResponse])
async def list_records(
    type: RecordType | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List financial records with filtering and pagination."""
    filters = RecordFilter(
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    return await record_service.list_records(db, user, filters, page=page, limit=limit)


@router.get("/export")
async def export_records(
    format: str = Query("csv", regex="^(csv|json)$"),
    type: RecordType | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ANALYST, UserRole.ADMIN)),
):
    """Export records as CSV or JSON (analyst + admin)."""
    filters = RecordFilter(type=type, category=category, date_from=date_from, date_to=date_to)
    result = await record_service.list_records(db, user, filters, page=1, limit=10000)
    records = result.items

    if format == "json":
        data = [r.model_dump(mode="json") for r in records]
        return StreamingResponse(
            io.BytesIO(json.dumps(data, indent=2, default=str).encode()),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=records.json"},
        )

    # CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "amount", "type", "category", "date", "description", "created_at"])
    for r in records:
        writer.writerow([
            str(r.id), str(r.amount), r.type.value, r.category,
            str(r.date), r.description or "", str(r.created_at),
        ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=records.csv"},
    )


@router.get("/{record_id}", response_model=RecordResponse)
async def get_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a single financial record."""
    return await record_service.get_record(db, record_id, user)


@router.put(
    "/{record_id}",
    response_model=RecordResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def update_record(
    record_id: uuid.UUID,
    body: RecordUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Update a financial record (admin only)."""
    return await record_service.update_record(db, record_id, user, body)


@router.delete(
    "/{record_id}",
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def delete_record(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Soft-delete a financial record (admin only)."""
    return await record_service.delete_record(db, record_id, user)
