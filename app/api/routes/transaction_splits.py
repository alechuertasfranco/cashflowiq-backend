# app/api/routes/transaction_splits.py

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.transaction_split import TransactionSplit
from app.models.split_settlement import SplitSettlement
from app.models.transaction import Transaction
from app.models.bank_account import BankAccount
from app.schemas.transaction_split import (
    TransactionSplitResponse,
    SplitSettlementCreate,
    SplitSettlementResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(tags=["Transaction Splits"])


def _enrich_split(split: TransactionSplit) -> dict:
    """Convert a TransactionSplit ORM object to a dict and inject currency fields."""
    data = TransactionSplitResponse.model_validate(split).model_dump()
    tx = split.transaction
    if tx is not None and tx.currency is not None:
        data["currency_code"] = tx.currency.code
        data["currency_symbol"] = tx.currency.symbol
    return data


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
        .options(
            joinedload(TransactionSplit.contact),
            joinedload(TransactionSplit.transaction).joinedload(Transaction.currency),
        )
        .filter(Transaction.user_id == current_user.id)
    )

    if settled is not None:
        query = query.filter(TransactionSplit.is_settled == settled)

    splits = (
        query.order_by(TransactionSplit.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_enrich_split(s) for s in splits]


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

    # Verify the destination account belongs to the current user.
    account = (
        db.query(BankAccount)
        .filter(
            BankAccount.id == data.to_account_id,
            BankAccount.user_id == current_user.id,
        )
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Record the contact's payment as a real income transaction so it
    # reflects on the destination account's balance.
    contact_name = split.contact.name if split.contact else "contacto"
    settlement_tx = Transaction(
        type="INCOME",
        amount=data.amount,
        description=f"Pago de {contact_name}",
        date=datetime.utcnow(),
        user_id=current_user.id,
        to_account_id=data.to_account_id,
        currency_id=account.currency_id,
    )
    db.add(settlement_tx)
    db.commit()
    db.refresh(settlement_tx)

    # Mark the split as settled.
    split.is_settled = True

    # Record the settlement, linked to the income transaction just created.
    settlement = SplitSettlement(
        split_id=split.id,
        amount=data.amount,
        date=datetime.utcnow(),
        transaction_id=settlement_tx.id,
    )
    db.add(settlement)
    db.commit()
    db.refresh(split)
    _ = split.contact

    return split
