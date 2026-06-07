# app/api/routes/transactions.py

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.transaction import Transaction
from app.models.bank_account import BankAccount
from app.models.credit_card import CreditCard
from app.models.transaction_split import TransactionSplit
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionResponse
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _get_or_404(db: Session, tx_id: int, user_id: int) -> Transaction:
    tx = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.id == tx_id, Transaction.user_id == user_id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


# 📥 GET TRANSACTIONS
@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    category_id: Optional[int] = None,
    account_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Transaction)
        .options(joinedload(Transaction.category))
        .filter(Transaction.user_id == current_user.id)
    )

    if type:
        query = query.filter(Transaction.type == type.upper())
    if from_date:
        query = query.filter(Transaction.date >= datetime.fromisoformat(from_date))
    if to_date:
        query = query.filter(Transaction.date <= datetime.fromisoformat(to_date))
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if account_id:
        query = query.filter(
            (Transaction.from_account_id == account_id)
            | (Transaction.to_account_id == account_id)
        )

    return query.order_by(Transaction.date.desc()).offset(offset).limit(limit).all()


# ➕ CREATE TRANSACTION
@router.post("", response_model=TransactionResponse)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx_type = data.type.upper()

    # Derive currency from the primary source if not provided
    currency_id = data.currency_id
    if currency_id is None:
        if data.account_id is not None:
            account = (
                db.query(BankAccount)
                .filter(BankAccount.id == data.account_id, BankAccount.user_id == current_user.id)
                .first()
            )
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")
            currency_id = account.currency_id
        elif data.credit_card_id is not None:
            card = (
                db.query(CreditCard)
                .filter(CreditCard.id == data.credit_card_id, CreditCard.user_id == current_user.id)
                .first()
            )
            if not card:
                raise HTTPException(status_code=404, detail="Credit card not found")
            currency_id = card.currency_id
        else:
            raise HTTPException(status_code=400, detail="account_id or credit_card_id is required")

    # Map account fields by transaction type
    from_account_id = None
    from_credit_card_id = None
    to_account_id = None

    if tx_type == "INCOME":
        to_account_id = data.account_id
    elif tx_type == "EXPENSE":
        if data.credit_card_id:
            from_credit_card_id = data.credit_card_id
        else:
            from_account_id = data.account_id
    elif tx_type == "TRANSFER":
        from_account_id = data.account_id
        to_account_id = data.to_account_id
        if not from_account_id or not to_account_id:
            raise HTTPException(
                status_code=400,
                detail="Transfer requires both account_id (source) and to_account_id (destination)",
            )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown transaction type: {data.type}")

    tx = Transaction(
        type=tx_type,
        amount=data.amount,
        description=data.description,
        date=data.date or datetime.utcnow(),
        user_id=current_user.id,
        from_account_id=from_account_id,
        from_credit_card_id=from_credit_card_id,
        to_account_id=to_account_id,
        category_id=data.category_id,
        currency_id=currency_id,
        is_recurring=data.is_recurring,
        is_fixed=data.is_fixed,
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)

    # Create split rows if provided.
    if data.splits:
        for item in data.splits:
            split = TransactionSplit(
                transaction_id=tx.id,
                contact_id=item.contact_id,
                amount=item.amount,
                is_settled=False,
            )
            db.add(split)
        db.commit()

    _ = tx.category

    return tx


# 🔍 GET SINGLE TRANSACTION
@router.get("/{tx_id}", response_model=TransactionResponse)
def get_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_or_404(db, tx_id, current_user.id)


# ✏️ UPDATE TRANSACTION
@router.put("/{tx_id}", response_model=TransactionResponse)
def update_transaction(
    tx_id: int,
    data: TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = _get_or_404(db, tx_id, current_user.id)

    if data.type is not None:
        tx.type = data.type.upper()
    if data.amount is not None:
        tx.amount = data.amount
    if data.description is not None:
        tx.description = data.description
    if data.date is not None:
        tx.date = data.date
    if data.category_id is not None:
        tx.category_id = data.category_id
    if data.currency_id is not None:
        tx.currency_id = data.currency_id
    if data.is_recurring is not None:
        tx.is_recurring = data.is_recurring
    if data.is_fixed is not None:
        tx.is_fixed = data.is_fixed

    # Re-map account fields if type or account_id changed
    if data.account_id is not None:
        tx_type = tx.type
        if tx_type == "INCOME":
            tx.to_account_id = data.account_id
        else:
            tx.from_account_id = data.account_id

    db.commit()
    db.refresh(tx)
    _ = tx.category

    return tx


# ❌ DELETE TRANSACTION
@router.delete("/{tx_id}")
def delete_transaction(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == tx_id, Transaction.user_id == current_user.id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(tx)
    db.commit()

    return {"message": "Deleted successfully"}
