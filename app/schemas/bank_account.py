# app/schemas/bank_account.py

from pydantic import BaseModel


class BankAccountBase(BaseModel):
    name: str
    initial_amount: float
    currency: str


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BankAccountBase):
    pass


class BankAccountResponse(BankAccountBase):
    id: int

    class Config:
        from_attributes = True
