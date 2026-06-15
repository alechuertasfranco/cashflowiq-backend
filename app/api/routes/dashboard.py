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
       sum of EXPENSE/TRANSFER debited from it), sorted by balance descending.
    - most_active_account_*: account with the most transactions this month.
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

    # --- All-time income / expense aggregates ---
    all_time_totals = (
        db.query(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == "INCOME", Transaction.amount),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("all_income"),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == "EXPENSE", Transaction.amount),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("all_expense"),
        )
        .filter(Transaction.user_id == current_user.id)
        .one()
    )

    all_time_income = all_time_totals.all_income or Decimal("0")
    all_time_expense = all_time_totals.all_expense or Decimal("0")

    # --- All-time per-account running balances ---
    accounts = (
        db.query(BankAccount)
        .options(joinedload(BankAccount.currency), joinedload(BankAccount.bank_entity))
        .filter(BankAccount.user_id == current_user.id)
        .all()
    )

    # Aggregate credits to each account across all time.
    # INCOME: money flowing in from outside (salary, freelance, etc.) — to_account_id is set.
    # TRANSFER: money arriving from another internal account — to_account_id is set.
    # Credit-card payment transfers (to_credit_card_id set, to_account_id NULL) are
    # correctly excluded here because to_account_id IS NOT NULL filters them out.
    credits_rows = (
        db.query(
            Transaction.to_account_id.label("account_id"),
            func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type.in_(["INCOME", "TRANSFER"]),
            Transaction.to_account_id.isnot(None),
        )
        .group_by(Transaction.to_account_id)
        .all()
    )
    credits_map = {row.account_id: row.total for row in credits_rows}

    # Aggregate debits from each account across all time.
    # EXPENSE: money leaving the account for external spending.
    # TRANSFER: money leaving the account to another account OR to a credit card
    #   (credit-card payment: from_account_id is set, to_credit_card_id is set,
    #    to_account_id is NULL — this is correctly captured here because we only
    #    require from_account_id IS NOT NULL).
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

    account_balances = sorted(
        [
            AccountBalance(
                id=account.id,
                name=account.name,
                currency_code=account.currency.code,
                bank_entity_code=account.bank_entity.code,
                balance=(
                    account.initial_amount
                    + credits_map.get(account.id, Decimal("0"))
                    - debits_map.get(account.id, Decimal("0"))
                ),
            )
            for account in accounts
        ],
        key=lambda a: a.balance,
        reverse=True,
    )

    # --- Most active account this month (by transaction count) ---
    monthly_txs = (
        db.query(Transaction.from_account_id, Transaction.to_account_id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= month_start,
            Transaction.date <= now,
        )
        .all()
    )

    account_tx_count: dict[int, int] = {}
    for tx in monthly_txs:
        if tx.from_account_id is not None:
            account_tx_count[tx.from_account_id] = account_tx_count.get(tx.from_account_id, 0) + 1
        if tx.to_account_id is not None:
            account_tx_count[tx.to_account_id] = account_tx_count.get(tx.to_account_id, 0) + 1

    most_active_id = None
    most_active_name = None
    most_active_count = 0
    if account_tx_count:
        most_active_id = max(account_tx_count, key=lambda k: account_tx_count[k])
        most_active_count = account_tx_count[most_active_id]
        most_active_name = next(
            (acc.name for acc in accounts if acc.id == most_active_id), None
        )

    return DashboardSummary(
        total_income=total_income,
        total_expense=total_expense,
        net_balance=net_balance,
        all_time_income=all_time_income,
        all_time_expense=all_time_expense,
        accounts=account_balances,
        most_active_account_id=most_active_id,
        most_active_account_name=most_active_name,
        most_active_account_tx_count=most_active_count,
    )
