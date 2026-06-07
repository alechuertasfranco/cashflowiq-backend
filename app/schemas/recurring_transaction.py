# app/schemas/recurring_transaction.py

from typing import Optional
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel

from app.schemas.category import CategoryResponse


class RecurringTransactionCreate(BaseModel):
    name: str
    amount: Decimal
    type: str           # INCOME | EXPENSE
    frequency: str      # DAILY | WEEKLY | MONTHLY | YEARLY
    next_execution_date: datetime
    end_date: Optional[date] = None
    category_id: int
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    currency_id: Optional[int] = None


class RecurringTransactionUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    type: Optional[str] = None
    frequency: Optional[str] = None
    next_execution_date: Optional[datetime] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    currency_id: Optional[int] = None


class RecurringTransactionResponse(BaseModel):
    id: int
    name: str
    amount: Decimal
    type: str
    frequency: str
    next_execution_date: datetime
    end_date: Optional[date] = None
    is_active: bool
    category_id: int
    category: CategoryResponse
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    currency_id: Optional[int] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
