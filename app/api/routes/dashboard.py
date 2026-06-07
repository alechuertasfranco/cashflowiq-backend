# app/api/routes/dashboard.py

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, case
from sqlalchemy.orm import Session, joinedload

from app.dependencies.current_user import get_current_user, get_db
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import AccountBalance, DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a financial snapshot for the authenticated user:

    - total_income / total_expense: sum of transactions in the current
      calendar month (UTC, INCOME and EXPENSE types respectively).
    - net_balance: total_income - total_expense.
    - accounts: every BankAccount with its all-time running balance
      (initial_amount + sum of INCOME credited to it -
       sum of EXPENSE/TRANSFER debited from it).
    """
    now = datetime.now(timezone.utc)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    # --- Current-month income / expense aggregates ---
    monthly_totals = (
        db.query(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == "INCOME", Transaction.amount),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == "EXPENSE", Transaction.amount),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("total_expense"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= month_start,
            Transaction.date <= now,
        )
        .one()
    )

    total_income = monthly_totals.total_income or Decimal("0")
    total_expense = monthly_totals.total_expense or Decimal("0")
    net_balance = total_income - total_expense

    # --- All-time per-account running balances ---
    accounts = (
        db.query(BankAccount)
        .options(joinedload(BankAccount.currency))
        .filter(BankAccount.user_id == current_user.id)
        .all()
    )

    # Aggregate credits (INCOME to each account) across all time.
    credits_rows = (
        db.query(
            Transaction.to_account_id.label("account_id"),
            func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "INCOME",
            Transaction.to_account_id.isnot(None),
        )
        .group_by(Transaction.to_account_id)
        .all()
    )
    credits_map = {row.account_id: row.total for row in credits_rows}

    # Aggregate debits (EXPENSE or TRANSFER from each account) across all time.
    debits_rows = (
        db.query(
            Transaction.from_account_id.label("account_id"),
            func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type.in_(["EXPENSE", "TRANSFER"]),
            Transaction.from_account_id.isnot(None),
        )
        .group_by(Transaction.from_account_id)
        .all()
    )
    debits_map = {row.account_id: row.total for row in debits_rows}

    account_balances = [
        AccountBalance(
            id=account.id,
            name=account.name,
            currency_code=account.currency.code,
            balance=(
                account.initial_amount
                + credits_map.get(account.id, Decimal("0"))
                - debits_map.get(account.id, Decimal("0"))
            ),
        )
        for account in accounts
    ]

    return DashboardSummary(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,
        accounts=account_balances,
    )
