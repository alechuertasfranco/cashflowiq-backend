# app/schemas/transaction.py

from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

from app.schemas.category import CategoryResponse
from app.schemas.currency import CurrencyResponse


class TransactionBase(BaseModel):
    type: str  # INCOME | EXPENSE | TRANSFER
    amount: Decimal
    description: Optional[str] = None
    date: Optional[datetime] = None

    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    investment_fund_id: Optional[int] = None

    category_id: Optional[int] = None
    currency_id: int

    is_recurring: Optional[bool] = False
    is_fixed: Optional[bool] = False


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    investment_fund_id: Optional[int] = None

    category_id: Optional[int] = None
    currency_id: Optional[int] = None

    is_recurring: Optional[bool] = None
    is_fixed: Optional[bool] = None


class TransactionResponse(BaseModel):
    id: int

    type: str
    amount: Decimal
    description: Optional[str]
    date: datetime

    account_id: Optional[int]
    credit_card_id: Optional[int]
    investment_fund_id: Optional[int]

    category_id: Optional[int]
    category: Optional[CategoryResponse]

    currency_id: int
    currency: CurrencyResponse

    is_recurring: bool
    is_fixed: bool

    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
