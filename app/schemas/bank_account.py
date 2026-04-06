# app/schemas/bank_account.py

from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from app.schemas.currency import CurrencyResponse
from app.schemas.bank_entity import BankEntityResponse


class BankAccountBase(BaseModel):
    name: str
    initial_amount: Decimal
    currency_id: int
    bank_entity_id: int


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BaseModel):
    name: Optional[str] = None
    initial_amount: Optional[Decimal] = None
    currency_id: Optional[int] = None
    bank_entity_id: Optional[int] = None


class BankAccountResponse(BaseModel):
    id: int
    name: str
    initial_amount: Decimal

    currency_id: int
    currency: CurrencyResponse

    bank_entity_id: int
    bank_entity: BankEntityResponse

    user_id: int

    class Config:
        from_attributes = True
