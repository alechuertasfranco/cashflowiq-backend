"""app/schemas/budget.py"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from app.schemas.currency import CurrencyResponse


class BudgetBase(BaseModel):
    """Base schema for budget."""

    amount: Decimal
    currency_id: int
    category_id: int


class BudgetCreate(BudgetBase):
    """Schema for creating a budget."""


class BudgetUpdate(BaseModel):
    """Schema for updating a budget."""

    amount: Optional[Decimal] = None


class BudgetResponse(BaseModel):
    """
    Budget response including computed spending.

    'spent' representa cuánto se ha gastado en la categoría
    en el mes actual.
    """

    id: int
    amount: Decimal
    category_id: int
    user_id: int

    currency_id: int
    currency: CurrencyResponse

    spent: Decimal = 0

    created_at: datetime

    class Config:
        """Pydantic configuration for BudgetResponse."""

        from_attributes = True
