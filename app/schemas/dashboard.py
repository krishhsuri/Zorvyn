"""Pydantic schemas for the analytics / dashboard endpoints."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.record import RecordResponse


class SummaryResponse(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal
    record_count: int


class CategoryBreakdown(BaseModel):
    category: str
    total: Decimal
    count: int
    percentage: float


class TrendPoint(BaseModel):
    period: str           # e.g. "2026-03" or "2026-W14"
    income: Decimal
    expense: Decimal
    balance: Decimal


class RecentActivityResponse(BaseModel):
    records: list[RecordResponse]
