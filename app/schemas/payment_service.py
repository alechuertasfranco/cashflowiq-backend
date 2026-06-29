from pydantic import BaseModel
from typing import Optional


class PaymentServiceCreate(BaseModel):
    name: str
    service_type: str = "generic"
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None


class PaymentServiceUpdate(BaseModel):
    name: Optional[str] = None
    service_type: Optional[str] = None
    account_id: Optional[int] = None
    credit_card_id: Optional[int] = None


class PaymentServiceResponse(BaseModel):
    id: int
    user_id: int
    name: str
    service_type: str
    account_id: Optional[int]
    credit_card_id: Optional[int]

    class Config:
        from_attributes = True
