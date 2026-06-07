# app/schemas/reports.py

from decimal import Decimal
from pydantic import BaseModel


class CashflowReport(BaseModel):
    """Monthly cashflow summary for the authenticated user."""

    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    fixed_expense: Decimal
    variable_expense: Decimal
    savings_rate: float

    class Config:
        from_attributes = True


class CategoryReport(BaseModel):
    """Spending (or income) breakdown by category for a given month."""

    category_id: int
    category_name: str
    total: Decimal
    percentage: float

    class Config:
        from_attributes = True


class EntityReport(BaseModel):
    """Income / expense breakdown by bank entity for a given month."""

    entity_id: int
    entity_name: str
    total_income: Decimal
    total_expense: Decimal
    net: Decimal

    class Config:
        from_attributes = True
