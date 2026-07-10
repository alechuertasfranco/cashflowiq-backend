# app\api\routes\investment_fund.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.investment_fund import InvestmentFund
from app.models.investment_fund_snapshot import InvestmentFundSnapshot
from app.schemas.investment_fund import (
    InvestmentFundCreate,
    InvestmentFundUpdate,
    InvestmentFundResponse,
)
from app.schemas.investment_fund_snapshot import (
    InvestmentFundSnapshotCreate,
    InvestmentFundSnapshotResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/investment-funds", tags=["Investment Funds"])


# 📥 GET FUNDS
@router.get("", response_model=list[InvestmentFundResponse])
def get_funds(
    limit: int = 50,
    offset: int = 0,
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
        .offset(offset)
        .limit(limit)
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
        current_value=fund.current_value,
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
    existing.current_value = fund.current_value
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


# --- Snapshot sub-resources ---

def _get_fund_or_404(fund_id: int, user_id: int, db: Session) -> InvestmentFund:
    fund = (
        db.query(InvestmentFund)
        .filter(
            InvestmentFund.id == fund_id,
            InvestmentFund.user_id == user_id,
        )
        .first()
    )
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    return fund


def _sync_current_value_from_snapshots(fund: InvestmentFund, db: Session) -> None:
    """Keep current_value in lockstep with the most recent snapshot.

    current_value used to be a field the user only set by hand when creating
    the fund, so it never moved after that — "Valor actual" kept showing the
    original number forever even after registering new monthly balances.
    The latest snapshot (by date) is now the source of truth for it.
    """
    latest = (
        db.query(InvestmentFundSnapshot)
        .filter(InvestmentFundSnapshot.investment_fund_id == fund.id)
        .order_by(InvestmentFundSnapshot.snapshot_date.desc())
        .first()
    )
    fund.current_value = float(latest.value) if latest else None


# GET /investment-funds/{fund_id}/snapshots
@router.get("/{fund_id}/snapshots", response_model=list[InvestmentFundSnapshotResponse])
def get_snapshots(
    fund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_fund_or_404(fund_id, current_user.id, db)
    return (
        db.query(InvestmentFundSnapshot)
        .filter(
            InvestmentFundSnapshot.investment_fund_id == fund_id,
            InvestmentFundSnapshot.user_id == current_user.id,
        )
        .order_by(InvestmentFundSnapshot.snapshot_date.asc())
        .all()
    )


# POST /investment-funds/{fund_id}/snapshots
@router.post("/{fund_id}/snapshots", response_model=InvestmentFundSnapshotResponse, status_code=201)
def create_snapshot(
    fund_id: int,
    snapshot: InvestmentFundSnapshotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fund = _get_fund_or_404(fund_id, current_user.id, db)
    new_snapshot = InvestmentFundSnapshot(
        investment_fund_id=fund_id,
        user_id=current_user.id,
        snapshot_date=snapshot.snapshot_date,
        value=snapshot.value,
    )
    db.add(new_snapshot)
    db.flush()
    _sync_current_value_from_snapshots(fund, db)
    db.commit()
    db.refresh(new_snapshot)
    return new_snapshot


# DELETE /investment-funds/{fund_id}/snapshots/{snapshot_id}
@router.delete("/{fund_id}/snapshots/{snapshot_id}")
def delete_snapshot(
    fund_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fund = _get_fund_or_404(fund_id, current_user.id, db)
    existing = (
        db.query(InvestmentFundSnapshot)
        .filter(
            InvestmentFundSnapshot.id == snapshot_id,
            InvestmentFundSnapshot.investment_fund_id == fund_id,
            InvestmentFundSnapshot.user_id == current_user.id,
        )
        .first()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    db.delete(existing)
    db.flush()
    _sync_current_value_from_snapshots(fund, db)
    db.commit()
    return {"message": "Deleted successfully"}
