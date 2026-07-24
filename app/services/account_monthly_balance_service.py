# app/services/account_monthly_balance_service.py
#
# Monthly-balance snapshot system for bank accounts.
#
# Goal: avoid summing an account's entire transaction history on every read
# (dashboard, balance lookups). Instead we persist one closed-month snapshot
# row per (account, year, month) in `account_monthly_balances`, chained off
# the previous month's `final_balance`. Live reads then only need to add the
# current (still-open) month's deltas on top of the latest closed snapshot.
#
# Correctness invariant: the snapshot chain must always produce the exact
# same balance as summing every transaction since account creation. This
# holds because each month's initial_balance is defined as the previous
# month's final_balance (or the account's initial_amount for the very first
# month), and final_balance = initial_balance + inflow - outflow for that
# month alone — so the chain telescopes into the same all-time sum.
#
# Only the current UTC calendar month is ever left un-snapshotted (it's
# still "open" — more transactions can land in it today). Every month
# strictly before the current one is a "closed" month and is safe to
# snapshot permanently; closed-month snapshots never change again unless a
# backdated transaction lands in (or a past transaction is edited/deleted
# out of) that month, in which case the cascade re-recomputes it and every
# closed month after it.

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.account_monthly_balance import AccountMonthlyBalance
from app.models.bank_account import BankAccount
from app.models.transaction import Transaction


def _prev_month(year: int, month: int) -> tuple[int, int]:
    """Return the (year, month) immediately preceding the given (year, month)."""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def _month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    """Return (month_start, month_end) as tz-aware UTC datetimes, [start, end)."""
    month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        month_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        month_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return month_start, month_end


def recompute_account_month(
    db: Session, account: BankAccount, year: int, month: int
) -> AccountMonthlyBalance:
    """
    Recompute (and upsert) the snapshot row for a single (account, year, month).

    initial_balance is chained off the previous month's snapshot if one
    exists, otherwise it falls back to the account's initial_amount (i.e.
    this is being computed as the account's very first closed month).

    Does NOT commit — the caller owns the transaction. Uses `db.flush()` so
    that the upserted/updated row is visible to subsequent queries within
    the same session immediately (this project's SessionLocal is configured
    with autoflush=False, so we can't rely on implicit autoflush to make a
    pending change visible to the next iteration's query).
    """
    prev_year, prev_month = _prev_month(year, month)
    prev_snapshot = (
        db.query(AccountMonthlyBalance)
        .filter(
            AccountMonthlyBalance.account_id == account.id,
            AccountMonthlyBalance.year == prev_year,
            AccountMonthlyBalance.month == prev_month,
        )
        .first()
    )

    if prev_snapshot is not None:
        initial_balance = prev_snapshot.final_balance
    else:
        initial_balance = account.initial_amount

    month_start, month_end = _month_bounds(year, month)

    total_inflow = (
        db.query(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
        .filter(
            Transaction.to_account_id == account.id,
            Transaction.type.in_(["INCOME", "TRANSFER"]),
            Transaction.date >= month_start,
            Transaction.date < month_end,
        )
        .scalar()
    )

    total_outflow = (
        db.query(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
        .filter(
            Transaction.from_account_id == account.id,
            Transaction.type.in_(["EXPENSE", "TRANSFER"]),
            Transaction.date >= month_start,
            Transaction.date < month_end,
        )
        .scalar()
    )

    final_balance = initial_balance + total_inflow - total_outflow

    snapshot = (
        db.query(AccountMonthlyBalance)
        .filter(
            AccountMonthlyBalance.account_id == account.id,
            AccountMonthlyBalance.year == year,
            AccountMonthlyBalance.month == month,
        )
        .first()
    )

    if snapshot is not None:
        snapshot.initial_balance = initial_balance
        snapshot.final_balance = final_balance
        snapshot.total_inflow = total_inflow
        snapshot.total_outflow = total_outflow
    else:
        snapshot = AccountMonthlyBalance(
            user_id=account.user_id,
            account_id=account.id,
            year=year,
            month=month,
            initial_balance=initial_balance,
            final_balance=final_balance,
            total_inflow=total_inflow,
            total_outflow=total_outflow,
        )
        db.add(snapshot)

    # Ensure this row (insert or update) is visible to the next iteration's
    # query of this same (account, year, month+1) chain — SessionLocal in
    # this project has autoflush=False, so an explicit flush is required.
    db.flush()

    return snapshot


def recompute_affected_accounts(db: Session, pairs: set[tuple[int, int, int]]) -> None:
    """
    Recompute monthly-balance snapshots for a deduplicated set of
    (account_id, year, month) pairs affected by a transaction write, then
    commit those snapshot changes in a second, separate commit.

    For each affected account, the recompute doesn't just start at the
    transaction's own month — it also starts from the month right after
    that account's latest existing snapshot, whichever is earlier. A plain
    same-day transaction lands in the still-open current month, which by
    itself is a no-op for the snapshot chain; without this, an account that
    only ever gets "today"-dated transactions would never have last month's
    snapshot created once the calendar rolls over, and the dashboard would
    keep falling back to the unbounded all-time sum forever. Starting from
    latest-snapshot+1 makes every write also catch up any idle month gap.

    Safe to call with pairs referring to open/current months (a no-op) or
    already-correct closed months (idempotent) — callers don't need to
    pre-filter, just deduplicate.
    """
    if not pairs:
        return

    account_ids = {account_id for account_id, _year, _month in pairs}
    accounts = {
        acc.id: acc
        for acc in db.query(BankAccount).filter(BankAccount.id.in_(account_ids)).all()
    }

    starts: dict[int, tuple[int, int]] = {}
    for account_id, year, month in pairs:
        current = starts.get(account_id)
        if current is None or (year, month) < current:
            starts[account_id] = (year, month)

    for account_id in account_ids:
        account = accounts.get(account_id)
        if account is None:
            continue

        latest_snapshot = (
            db.query(AccountMonthlyBalance.year, AccountMonthlyBalance.month)
            .filter(AccountMonthlyBalance.account_id == account_id)
            .order_by(AccountMonthlyBalance.year.desc(), AccountMonthlyBalance.month.desc())
            .first()
        )
        if latest_snapshot is not None:
            next_year, next_month = latest_snapshot.year, latest_snapshot.month
            if next_month == 12:
                next_year, next_month = next_year + 1, 1
            else:
                next_month += 1
            candidate = (next_year, next_month)
            if candidate < starts[account_id]:
                starts[account_id] = candidate

        start_year, start_month = starts[account_id]
        recompute_account_from_month(db, account, start_year, start_month)

    db.commit()


def recompute_account_from_month(db: Session, account: BankAccount, year: int, month: int) -> None:
    """
    Recompute and chain snapshots for every closed month starting at
    (year, month) up to (but not including) the current UTC calendar month.

    The current, still-open month is never snapshotted by design — live
    balance reads add its deltas on top of the latest closed snapshot
    instead. If (year, month) is already the current month or later, this
    is a no-op.
    """
    now = datetime.now(timezone.utc)
    current_year, current_month = now.year, now.month

    y, m = year, month
    while (y, m) < (current_year, current_month):
        recompute_account_month(db, account, y, m)
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1


def get_account_balance(db: Session, account: BankAccount) -> Decimal:
    """
    Return an account's current balance using the snapshot chain.

    Uses the closed-month snapshot for the month immediately before the
    current UTC calendar month (if it exists) as a base, plus current-month
    deltas on top. Falls back to the account's initial_amount plus an
    unbounded (all-time) transaction sum when no closed-month snapshot
    exists yet (brand-new account) — this matches the pre-snapshot
    behavior exactly for accounts with no history.
    """
    now = datetime.now(timezone.utc)
    current_year, current_month = now.year, now.month
    prev_year, prev_month = _prev_month(current_year, current_month)

    snapshot = (
        db.query(AccountMonthlyBalance)
        .filter(
            AccountMonthlyBalance.account_id == account.id,
            AccountMonthlyBalance.year == prev_year,
            AccountMonthlyBalance.month == prev_month,
        )
        .first()
    )

    if snapshot is not None:
        base = snapshot.final_balance
        date_filter = Transaction.date >= _month_bounds(current_year, current_month)[0]
    else:
        base = account.initial_amount
        date_filter = None

    inflow_query = db.query(
        func.coalesce(func.sum(Transaction.amount), Decimal("0"))
    ).filter(
        Transaction.to_account_id == account.id,
        Transaction.type.in_(["INCOME", "TRANSFER"]),
    )
    outflow_query = db.query(
        func.coalesce(func.sum(Transaction.amount), Decimal("0"))
    ).filter(
        Transaction.from_account_id == account.id,
        Transaction.type.in_(["EXPENSE", "TRANSFER"]),
    )

    if date_filter is not None:
        inflow_query = inflow_query.filter(date_filter)
        outflow_query = outflow_query.filter(date_filter)

    inflow = inflow_query.scalar()
    outflow = outflow_query.scalar()

    return base + inflow - outflow
