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
    type: str  # INCOME | EXPENSE | TRANSFER
    description: Optional[str] = None
    category_id: Optional[int] = None

    # For TRANSFER lines: whether the money came INTO the statement account
    # (True) or left it (False). Derived from the statement's abono/cargo
    # column. A statement-import transfer is recorded one-sided (only the
    # statement account's leg) so importing each account's statement never
    # double-counts the same transfer.
    is_inflow: bool = True


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
