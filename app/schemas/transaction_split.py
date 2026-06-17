# app/schemas/transaction_split.py

from typing import Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel

from app.schemas.contact import ContactResponse


class SplitItemCreate(BaseModel):
    """Embedded in TransactionCreate.splits."""
    contact_id: int
    amount: Decimal


class TransactionSplitResponse(BaseModel):
    id: int
    transaction_id: int
    contact_id: Optional[int] = None
    contact: Optional[ContactResponse] = None
    amount: Decimal
    is_settled: bool
    created_at: Optional[datetime] = None
    currency_code: Optional[str] = None
    currency_symbol: Optional[str] = None

    class Config:
        from_attributes = True


class SplitSettlementCreate(BaseModel):
    amount: Decimal
    to_account_id: int  # account that received the contact's payment


class SplitSettlementResponse(BaseModel):
    id: int
    split_id: int
    amount: Decimal
    date: Optional[datetime] = None
    transaction_id: Optional[int] = None
    to_account_id: Optional[int] = None

    class Config:
        from_attributes = True
