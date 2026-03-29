# app/schemas/bank_account.py

from pydantic import BaseModel
from typing import Optional


class BankAccountBase(BaseModel):
    name: str
    initial_amount: float
    currency: str
    bank_entity_id: Optional[int] = None


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BankAccountBase):
    pass


class BankAccountResponse(BankAccountBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
