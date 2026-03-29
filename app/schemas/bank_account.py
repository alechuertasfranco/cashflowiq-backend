# app/schemas/bank_account.py

from pydantic import BaseModel, Field
from typing import Optional


class BankAccountBase(BaseModel):
    name: str = Field(..., min_length=1)
    initial_amount: float
    currency: str
    bank_entity_id: Optional[int] = None


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BankAccountBase):
    pass


class BankAccountResponse(BankAccountBase):
    id: int

    class Config:
        from_attributes = True
