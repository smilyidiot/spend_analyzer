"""Pydantic models describing the analytics report returned by the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Summary(BaseModel):
    total_spend: float
    transaction_count: int
    average_transaction: float
    median_transaction: float
    distinct_vendors: int
    distinct_categories: int
    start_date: str
    end_date: str
    currency: str


class CategoryRow(BaseModel):
    category: str
    total: float
    count: int
    share_pct: float


class VendorRow(BaseModel):
    vendor: str
    total: float
    count: int


class MonthRow(BaseModel):
    month: str
    total: float
    mom_change_pct: float | None = None


class OutlierRow(BaseModel):
    date: str
    vendor: str
    category: str
    amount: float


class DuplicateRow(BaseModel):
    vendor: str
    amount: float
    occurrences: int
    dates: list[str]
    recoverable: float


class Report(BaseModel):
    summary: Summary
    by_category: list[CategoryRow]
    by_vendor: list[VendorRow]
    by_month: list[MonthRow]
    outliers: list[OutlierRow]
    duplicate_suspects: list[DuplicateRow]
    potential_recovery: float
    insights: list[str] = Field(default_factory=list)
