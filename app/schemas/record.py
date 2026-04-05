"""Pydantic schemas for FinancialRecord CRUD + filtering."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.models.record import RecordType

T = TypeVar("T")


class RecordCreate(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2, description="Must be positive")
    type: RecordType
    category: str = Field(min_length=1, max_length=50)
    date: date
    description: str | None = None


class RecordUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    type: RecordType | None = None
    category: str | None = Field(None, min_length=1, max_length=50)
    date: date | None = None
    description: str | None = None


class RecordResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    amount: Decimal
    type: RecordType
    category: str
    date: date
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordFilter(BaseModel):
    """Query parameters for filtering records."""
    type: RecordType | None = None
    category: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    search: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated wrapper."""
    items: list[T]
    total: int
    page: int
    limit: int
    pages: int
