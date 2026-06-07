# app/schemas/credit_card.py

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from app.schemas.currency import CurrencyResponse
from app.schemas.bank_entity import BankEntityResponse


class CreditCardBase(BaseModel):
    name: str
    credit_limit: Decimal
    brand: str
    closing_day: int
    due_day: int
    interest_rate: Optional[Decimal] = None
    currency_id: int
    bank_entity_id: int


class CreditCardCreate(CreditCardBase):
    pass


class CreditCardUpdate(BaseModel):
    name: Optional[str] = None
    credit_limit: Optional[Decimal] = None
    brand: Optional[str] = None
    closing_day: Optional[int] = None
    due_day: Optional[int] = None
    interest_rate: Optional[Decimal] = None
    currency_id: Optional[int] = None
    bank_entity_id: Optional[int] = None


class CreditCardResponse(BaseModel):
    id: int
    name: str
    credit_limit: Decimal
    brand: str
    closing_day: int
    due_day: int
    interest_rate: Optional[Decimal]
    used_amount: float

    currency_id: int
    currency: CurrencyResponse

    bank_entity_id: int
    bank_entity: BankEntityResponse

    user_id: int

    class Config:
        from_attributes = True
