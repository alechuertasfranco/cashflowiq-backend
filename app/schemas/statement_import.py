# app/schemas/statement_import.py

from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel

from app.schemas.transaction import TransactionResponse


class StatementLineCreate(BaseModel):
    """One reconciled movement the client confirmed as new (to be created)."""

    date: datetime
    amount: Decimal
    type: str  # INCOME | EXPENSE
    description: Optional[str] = None
    category_id: Optional[int] = None


class StatementImportCreate(BaseModel):
    account_id: int
    year: int
    month: int
    filename: str
    bank: Optional[str] = None
    items: List[StatementLineCreate]


class StatementImportResponse(BaseModel):
    id: int
    account_id: int
    year: int
    month: int
    filename: str
    bank: Optional[str] = None
    imported_count: int
    created_at: datetime

    # Populated only on detail (GET /{id}) and create responses.
    transactions: List[TransactionResponse] = []

    class Config:
        from_attributes = True
