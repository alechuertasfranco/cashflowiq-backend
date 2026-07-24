# app\api\routes\bank_accounts.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.bank_account import BankAccount
from app.models.transaction import Transaction
from app.models.account_monthly_balance import AccountMonthlyBalance
from app.schemas.bank_account import (
    BankAccountCreate,
    BankAccountUpdate,
    BankAccountResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/bank-accounts", tags=["Bank Accounts"])


def _compute_balance(db: Session, account: BankAccount) -> float:
    """Compute current balance = initial_amount + inflows - outflows."""
    inflows = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.to_account_id == account.id)
        .scalar()
    )
    outflows = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(Transaction.from_account_id == account.id)
        .scalar()
    )
    return float(account.initial_amount) + float(inflows) - float(outflows)


def _to_response(db: Session, account: BankAccount) -> BankAccountResponse:
    """Convert ORM object to response schema with computed balance."""
    return BankAccountResponse(
        id=account.id,
        name=account.name,
        initial_amount=account.initial_amount,
        current_balance=_compute_balance(db, account),
        currency_id=account.currency_id,
        currency=account.currency,
        bank_entity_id=account.bank_entity_id,
        bank_entity=account.bank_entity,
        user_id=account.user_id,
    )


# GET MOST-USED ACCOUNTS (by transaction count)
@router.get("/most-used", response_model=list[BankAccountResponse])
def get_most_used_accounts(
    limit: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage = (
        db.query(
            BankAccount.id,
            func.count(Transaction.id).label("usage_count"),  # pylint: disable=not-callable
        )
        .outerjoin(
            Transaction,
            (Transaction.from_account_id == BankAccount.id)
            | (Transaction.to_account_id == BankAccount.id),
        )
        .filter(BankAccount.user_id == current_user.id)
        .group_by(BankAccount.id)
        .order_by(func.count(Transaction.id).desc())  # pylint: disable=not-callable
        .limit(limit)
        .subquery()
    )

    accounts = (
        db.query(BankAccount)
        .options(joinedload(BankAccount.bank_entity), joinedload(BankAccount.currency))
        .filter(BankAccount.id.in_(db.query(usage.c.id)))
        .all()
    )

    # Preserve the order from the subquery
    id_order = {row.id: i for i, row in enumerate(db.query(usage.c.id, usage.c.usage_count).all())}
    accounts.sort(key=lambda a: id_order.get(a.id, 0))
    return [_to_response(db, a) for a in accounts]


# GET ACCOUNTS
@router.get("", response_model=list[BankAccountResponse])
def get_accounts(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts = (
        db.query(BankAccount)
        .options(joinedload(BankAccount.bank_entity), joinedload(BankAccount.currency))
        .filter(BankAccount.user_id == current_user.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_to_response(db, a) for a in accounts]


# GET SINGLE ACCOUNT
@router.get("/{account_id}", response_model=BankAccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(BankAccount)
        .options(joinedload(BankAccount.bank_entity), joinedload(BankAccount.currency))
        .filter(
            BankAccount.id == account_id,
            BankAccount.user_id == current_user.id,
        )
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return _to_response(db, account)


# GET MONTHLY BALANCE SNAPSHOT (for statement reconciliation)
@router.get("/{account_id}/monthly-balance")
def get_account_monthly_balance(
    account_id: int,
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the closed-month snapshot for (account, year, month) if it exists.

    Only months strictly before the current UTC month are snapshotted (a
    "closed" month). `closed` is True only when such a snapshot exists — the
    statement-import flow uses `final_balance` to verify the statement's closing
    balance agrees with the app's records before finalizing the import.
    """
    account = (
        db.query(BankAccount)
        .filter(BankAccount.id == account_id, BankAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    snapshot = (
        db.query(AccountMonthlyBalance)
        .filter(
            AccountMonthlyBalance.account_id == account_id,
            AccountMonthlyBalance.year == year,
            AccountMonthlyBalance.month == month,
        )
        .first()
    )

    if snapshot is None:
        return {
            "year": year,
            "month": month,
            "closed": False,
            "initial_balance": None,
            "final_balance": None,
        }

    return {
        "year": year,
        "month": month,
        "closed": True,
        "initial_balance": float(snapshot.initial_balance),
        "final_balance": float(snapshot.final_balance),
    }


# CREATE ACCOUNT
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
    _ = new_account.currency

    return _to_response(db, new_account)


# UPDATE ACCOUNT
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

    if account.name is not None:
        existing.name = account.name
    if account.initial_amount is not None:
        existing.initial_amount = account.initial_amount
    if account.currency_id is not None:
        existing.currency_id = account.currency_id
    if account.bank_entity_id is not None:
        existing.bank_entity_id = account.bank_entity_id

    db.commit()
    db.refresh(existing)
    _ = existing.bank_entity
    _ = existing.currency

    return _to_response(db, existing)


# DELETE ACCOUNT
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
