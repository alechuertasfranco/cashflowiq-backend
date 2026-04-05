# app/schemas/investment_fund.py

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from app.schemas.currency import CurrencyResponse
from app.schemas.bank_entity import BankEntityResponse


class InvestmentFundBase(BaseModel):
    name: str
    fund_type: Optional[str] = None
    invested_amount: Optional[Decimal] = None
    currency_id: int
    bank_entity_id: int


class InvestmentFundCreate(InvestmentFundBase):
    pass


class InvestmentFundUpdate(BaseModel):
    name: Optional[str] = None
    fund_type: Optional[str] = None
    invested_amount: Optional[Decimal] = None
    currency_id: Optional[int] = None
    bank_entity_id: Optional[int] = None


class InvestmentFundResponse(BaseModel):
    id: int
    name: str
    fund_type: Optional[str]
    invested_amount: Optional[Decimal]

    currency_id: int
    currency: CurrencyResponse

    bank_entity_id: int
    bank_entity: BankEntityResponse

    user_id: int

    class Config:
        from_attributes = True
