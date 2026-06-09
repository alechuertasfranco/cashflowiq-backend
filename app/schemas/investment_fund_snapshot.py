from pydantic import BaseModel
from datetime import date
from decimal import Decimal


class InvestmentFundSnapshotCreate(BaseModel):
    snapshot_date: date
    value: Decimal


class InvestmentFundSnapshotResponse(BaseModel):
    id: int
    investment_fund_id: int
    snapshot_date: date
    value: Decimal

    class Config:
        from_attributes = True
