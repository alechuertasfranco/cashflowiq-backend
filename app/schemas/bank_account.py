from pydantic import BaseModel
from typing import Optional
from app.schemas.bank_entity import BankEntityResponse


class BankAccountBase(BaseModel):
    name: str
    initial_amount: float
    currency: str
    bank_entity_id: Optional[int] = None


class BankAccountCreate(BankAccountBase):
    pass


class BankAccountUpdate(BankAccountBase):
    pass


class BankAccountResponse(BaseModel):
    id: int
    name: str
    initial_amount: float
    currency: str

    user_id: int

    bank_entity: BankEntityResponse

    class Config:
        from_attributes = True
