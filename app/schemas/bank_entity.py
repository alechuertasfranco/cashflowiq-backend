# app/schemas/bank_entity.py

from pydantic import BaseModel
from typing import Optional


class BankEntityBase(BaseModel):
    name: str
    code: str
    color: Optional[str] = None


class BankEntityCreate(BankEntityBase):
    pass


class BankEntityUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    color: Optional[str] = None


class BankEntityResponse(BankEntityBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
