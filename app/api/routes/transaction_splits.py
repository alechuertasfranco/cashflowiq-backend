# app/api/routes/transaction_splits.py

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.transaction_split import TransactionSplit
from app.models.split_settlement import SplitSettlement
from app.models.transaction import Transaction
from app.schemas.transaction_split import (
    TransactionSplitResponse,
    SplitSettlementCreate,
    SplitSettlementResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(tags=["Transaction Splits"])


# ---------------------------------------------------------------------------
# GET /transaction-splits
# ---------------------------------------------------------------------------

@router.get("/transaction-splits", response_model=list[TransactionSplitResponse])
def list_splits(
    settled: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all TransactionSplit rows that belong to the authenticated user.

    A split belongs to the user when its parent transaction's user_id matches.
    Optional `?settled=true|false` filters by is_settled.
    """
    query = (
        db.query(TransactionSplit)
        .join(Transaction, TransactionSplit.transaction_id == Transaction.id)
        .options(joinedload(TransactionSplit.contact))
        .filter(Transaction.user_id == current_user.id)
    )

    if settled is not None:
        query = query.filter(TransactionSplit.is_settled == settled)

    return (
        query.order_by(TransactionSplit.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# POST /split-settlements/{split_id}
# ---------------------------------------------------------------------------

@router.post(
    "/split-settlements/{split_id}",
    response_model=TransactionSplitResponse,
)
def settle_split(
    split_id: int,
    data: SplitSettlementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a split as settled and record the settlement amount."""
    # Load the split and verify it belongs to the current user via its transaction.
    split = (
        db.query(TransactionSplit)
        .join(Transaction, TransactionSplit.transaction_id == Transaction.id)
        .options(joinedload(TransactionSplit.contact))
        .filter(
            TransactionSplit.id == split_id,
            Transaction.user_id == current_user.id,
        )
        .first()
    )
    if not split:
        raise HTTPException(status_code=404, detail="Split not found")

    if split.is_settled:
        raise HTTPException(status_code=400, detail="Split is already settled")

    # Mark the split as settled.
    split.is_settled = True

    # Record the settlement.
    settlement = SplitSettlement(
        split_id=split.id,
        amount=data.amount,
        date=datetime.utcnow(),
    )
    db.add(settlement)
    db.commit()
    db.refresh(split)
    _ = split.contact

    return split
