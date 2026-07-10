# app/schemas/transaction_split.py

from typing import Optional
from decimal import Decimal
from datetime import datetime, timezone
from pydantic import BaseModel, field_serializer

from app.schemas.contact import ContactResponse


def _as_utc_iso(value: Optional[datetime]) -> Optional[str]:
    """Serialize a datetime that is stored naive (via datetime.utcnow) as an
    explicit UTC ISO string. Without the 'Z'/offset suffix, clients like
    Dart's DateTime.parse silently treat the UTC clock values as local time,
    which shows the wrong time (and sometimes the wrong day)."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


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

    @field_serializer('created_at')
    def _serialize_created_at(self, value: Optional[datetime]) -> Optional[str]:
        return _as_utc_iso(value)


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

    @field_serializer('date')
    def _serialize_date(self, value: Optional[datetime]) -> Optional[str]:
        return _as_utc_iso(value)
