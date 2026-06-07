# app/schemas/reports.py

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class CashflowReport(BaseModel):
    """Monthly cashflow summary for the authenticated user, per currency."""

    year: int
    month: int
    currency_code: str
    currency_symbol: str
    total_income: Decimal
    total_expense: Decimal
    fixed_expense: Decimal
    variable_expense: Decimal
    savings_rate: float

    class Config:
        from_attributes = True


class CategoryReport(BaseModel):
    """Spending (or income) breakdown by category for a given month, per currency."""

    category_id: int
    category_name: str
    parent_category_id: Optional[int] = None
    parent_category_name: Optional[str] = None
    currency_code: str
    currency_symbol: str
    total: Decimal
    percentage: float

    class Config:
        from_attributes = True


class EntityReport(BaseModel):
    """Income / expense breakdown by bank entity for a given month, per currency."""

    entity_id: int
    entity_name: str
    currency_code: str
    currency_symbol: str
    total_income: Decimal
    total_expense: Decimal
    net: Decimal

    class Config:
        from_attributes = True
