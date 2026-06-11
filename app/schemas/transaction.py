# app/schemas/transaction.py

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

class TransactionCategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    icon: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class SplitItemCreate(BaseModel):
    contact_id: int
    amount: Decimal


class TransactionCreate(BaseModel):
    type: str  # INCOME | EXPENSE | TRANSFER
    amount: Decimal
    description: Optional[str] = None
    date: Optional[datetime] = None

    # For INCOME: account_id = destination account
    # For EXPENSE: account_id = source account; credit_card_id = source card instead
    # For TRANSFER: account_id = source account, to_account_id = destination account
    #   Credit card payment TRANSFER: account_id = source account, to_credit_card_id = destination card
    account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    credit_card_id: Optional[int] = None
    to_credit_card_id: Optional[int] = None

    category_id: Optional[int] = None
    currency_id: Optional[int] = None  # derived from account if omitted

    is_recurring: bool = False
    is_fixed: bool = False

    # Set when this transaction is generated from a recurring rule (links them)
    recurring_transaction_id: Optional[int] = None

    # Optional split expense items
    splits: Optional[List[SplitItemCreate]] = None


class TransactionUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

    account_id: Optional[int] = None
    category_id: Optional[int] = None
    currency_id: Optional[int] = None

    is_recurring: Optional[bool] = None
    is_fixed: Optional[bool] = None


class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: Decimal
    description: Optional[str] = None
    date: datetime

    # account_id: computed via @property on the ORM model
    account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    to_credit_card_id: Optional[int] = None
    credit_card_id: Optional[int] = None   # source credit card for EXPENSE

    category_id: Optional[int] = None
    category: Optional[TransactionCategoryResponse] = None

    currency_id: int
    currency_code: str = ""
    currency_symbol: str = ""

    is_recurring: bool
    is_fixed: bool
    recurring_transaction_id: Optional[int] = None

    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
