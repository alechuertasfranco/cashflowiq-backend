# app\api\routes\investment_fund.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.investment_fund import InvestmentFund
from app.schemas.investment_fund import (
    InvestmentFundCreate,
    InvestmentFundUpdate,
    InvestmentFundResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/investment-funds", tags=["Investment Funds"])


# 📥 GET FUNDS
@router.get("", response_model=list[InvestmentFundResponse])
def get_funds(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(InvestmentFund)
        .options(
            joinedload(InvestmentFund.bank_entity),
            joinedload(InvestmentFund.currency),
        )
        .filter(InvestmentFund.user_id == current_user.id)
        .all()
    )


# ➕ CREATE FUND
@router.post("", response_model=InvestmentFundResponse)
def create_fund(
    fund: InvestmentFundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_fund = InvestmentFund(
        name=fund.name,
        fund_type=fund.fund_type,
        invested_amount=fund.invested_amount,
        currency_id=fund.currency_id,
        bank_entity_id=fund.bank_entity_id,
        user_id=current_user.id,
    )

    db.add(new_fund)
    db.commit()
    db.refresh(new_fund)

    _ = new_fund.bank_entity
    _ = new_fund.currency

    return new_fund


# ✏️ UPDATE FUND
@router.put("/{fund_id}", response_model=InvestmentFundResponse)
def update_fund(
    fund_id: int,
    fund: InvestmentFundUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(InvestmentFund)
        .filter(
            InvestmentFund.id == fund_id,
            InvestmentFund.user_id == current_user.id,
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Fund not found")

    existing.name = fund.name
    existing.fund_type = fund.fund_type
    existing.invested_amount = fund.invested_amount
    existing.currency_id = fund.currency_id
    existing.bank_entity_id = fund.bank_entity_id

    db.commit()
    db.refresh(existing)

    _ = existing.bank_entity
    _ = existing.currency

    return existing


# ❌ DELETE FUND
@router.delete("/{fund_id}")
def delete_fund(
    fund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(InvestmentFund)
        .filter(
            InvestmentFund.id == fund_id,
            InvestmentFund.user_id == current_user.id,
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Fund not found")

    db.delete(existing)
    db.commit()

    return {"message": "Deleted successfully"}
