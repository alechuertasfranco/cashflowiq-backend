# app\api\routes\bank_accounts.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.bank_account import BankAccount
from app.schemas.bank_account import (
    BankAccountCreate,
    BankAccountUpdate,
    BankAccountResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/bank-accounts", tags=["Bank Accounts"])


# 📥 GET ACCOUNTS
@router.get("", response_model=list[BankAccountResponse])
def get_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(BankAccount)
        .options(joinedload(BankAccount.bank_entity))
        .filter(BankAccount.user_id == current_user.id)
        .all()
    )


# ➕ CREATE ACCOUNT
@router.post("", response_model=BankAccountResponse)
def create_account(
    account: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_account = BankAccount(
        name=account.name,
        initial_amount=account.initial_amount,
        currency_id=account.currency_id,
        bank_entity_id=account.bank_entity_id,
        user_id=current_user.id,
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    _ = new_account.bank_entity

    return new_account


# ✏️ UPDATE ACCOUNT
@router.put("/{account_id}", response_model=BankAccountResponse)
def update_account(
    account_id: int,
    account: BankAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(BankAccount)
        .filter(
            BankAccount.id == account_id,
            BankAccount.user_id == current_user.id,
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")

    existing.name = account.name
    existing.initial_amount = account.initial_amount
    existing.currency_id = account.currency_id
    existing.bank_entity_id = account.bank_entity_id

    db.commit()
    db.refresh(existing)
    _ = existing.bank_entity

    return existing


# ❌ DELETE ACCOUNT
@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(BankAccount)
        .filter(
            BankAccount.id == account_id,
            BankAccount.user_id == current_user.id,
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(existing)
    db.commit()

    return {"message": "Deleted successfully"}
