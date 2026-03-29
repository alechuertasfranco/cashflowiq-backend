from pydantic import BaseModel
from typing import Optional


class BankEntityBase(BaseModel):
    name: str
    color: Optional[str] = None


class BankEntityCreate(BankEntityBase):
    pass


class BankEntityUpdate(BankEntityBase):
    pass


class BankEntityResponse(BankEntityBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
