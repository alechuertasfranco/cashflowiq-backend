# app/schemas/bank_account.py

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from app.schemas.bank_entity import BankEntityResponse


class BankAccountBase(BaseModel):
    name: str
    initial_amount: Decimal
    currency_id: str
    bank_entity_id: int


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BaseModel):
    name: Optional[str] = None
    initial_amount: Optional[Decimal] = None
    currency_id: Optional[str] = None
    bank_entity_id: Optional[int] = None


class BankAccountResponse(BaseModel):
    id: int
    name: str
    initial_amount: Decimal
    currency_id: int
    currency: CurrencyResponse

    user_id: int

    bank_entity: BankEntityResponse

    class Config:
        from_attributes = True
