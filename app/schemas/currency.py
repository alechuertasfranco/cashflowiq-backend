# app\schemas\currency.py

from pydantic import BaseModel
from decimal import Decimal
from typing import Optional


class CurrencyBase(BaseModel):
    code: str
    name: str
    symbol: str
    flag: Optional[str] = None
    decimals: int
    exchange_rate_to_base: Optional[Decimal] = None


class CurrencyResponse(CurrencyBase):
    id: int

    class Config:
        from_attributes = True
