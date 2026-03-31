# app\schemas\currency.py

from pydantic import BaseModel


class CurrencyBase(BaseModel):
    code: str
    name: str
    symbol: str


class CurrencyResponse(CurrencyBase):
    id: int

    class Config:
        from_attributes = True
