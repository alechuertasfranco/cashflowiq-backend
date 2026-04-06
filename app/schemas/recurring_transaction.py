# app/schemas/recurring_transaction.py

from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

from app.schemas.category import CategoryResponse


class RecurringTransactionBase(BaseModel):
    name: str
    amount: Decimal

    type: str  # INCOME | EXPENSE

    frequency: str  # DAILY | WEEKLY | MONTHLY | YEARLY
    next_execution_date: datetime

    category_id: int

    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None


class RecurringTransactionCreate(RecurringTransactionBase):
    pass


class RecurringTransactionUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    type: Optional[str] = None
    frequency: Optional[str] = None
    next_execution_date: Optional[datetime] = None
    category_id: Optional[int] = None

    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None


class RecurringTransactionResponse(BaseModel):
    id: int

    name: str
    amount: Decimal

    type: str
    frequency: str
    next_execution_date: datetime

    category_id: int
    category: CategoryResponse

    account_id: Optional[int]
    credit_card_id: Optional[int]

    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
