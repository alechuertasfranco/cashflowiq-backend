from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class BankEntityBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    color: Optional[str] = Field(None, regex=r"^[0-9A-Fa-f]{6}$")


class BankEntityCreate(BankEntityBase):
    pass


class BankEntityUpdate(BankEntityBase):
    pass


class BankEntityResponse(BankEntityBase):
    id: UUID

    class Config:
        from_attributes = True
