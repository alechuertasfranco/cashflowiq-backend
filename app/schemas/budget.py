# app/schemas/budget.py

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

from app.schemas.category import CategoryResponse


class BudgetBase(BaseModel):
    amount: Decimal
    category_id: int
    start_date: datetime
    end_date: datetime


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    amount: Optional[Decimal] = None
    category_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class BudgetResponse(BaseModel):
    id: int

    amount: Decimal

    category_id: int
    category: CategoryResponse

    start_date: datetime
    end_date: datetime

    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
