# app/api/routes/reports.py

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.dependencies.current_user import get_current_user, get_db
from app.models.bank_account import BankAccount
from app.models.bank_entity import BankEntity
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.reports import CashflowReport, CategoryReport, EntityReport

router = APIRouter(prefix="/reports", tags=["Reports"])


def _month_bounds(year: int, month: int):
    """Return (month_start, month_end) as naive UTC datetimes."""
    month_start = datetime(year, month, 1, tzinfo=timezone.utc)
    # Roll over to the first day of the next month then subtract nothing —
    # we use a strict < month_end comparison, so we only need the first
    # instant of the following month.
    if month == 12:
        month_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        month_end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    return month_start, month_end


# ---------------------------------------------------------------------------
# GET /reports/cashflow
# ---------------------------------------------------------------------------


@router.get("/cashflow", response_model=CashflowReport)
def get_cashflow_report(
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a cashflow summary for the requested month.

    Defaults to the current UTC year / month when omitted.
    """
    now = datetime.now(timezone.utc)
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    month_start, month_end = _month_bounds(year, month)

    row = (
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
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.type == "EXPENSE") & (Transaction.is_fixed == True),  # noqa: E712  # pylint: disable=singleton-comparison
                            Transaction.amount,
                        ),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("fixed_expense"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Transaction.type == "EXPENSE") & (Transaction.is_fixed == False),  # noqa: E712  # pylint: disable=singleton-comparison
                            Transaction.amount,
                        ),
                        else_=Decimal("0"),
                    )
                ),
                Decimal("0"),
            ).label("variable_expense"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= month_start,
            Transaction.date < month_end,
        )
        .one()
    )

    total_income = row.total_income or Decimal("0")
    total_expense = row.total_expense or Decimal("0")
    fixed_expense = row.fixed_expense or Decimal("0")
    variable_expense = row.variable_expense or Decimal("0")

    if total_income > 0:
        savings_rate = float((total_income - total_expense) / total_income * 100)
    else:
        savings_rate = 0.0

    return CashflowReport(
        year=year,
        month=month,
        total_income=total_income,
        total_expense=total_expense,
        fixed_expense=fixed_expense,
        variable_expense=variable_expense,
        savings_rate=savings_rate,
    )


# ---------------------------------------------------------------------------
# GET /reports/by-category
# ---------------------------------------------------------------------------


@router.get("/by-category", response_model=list[CategoryReport])
def get_by_category_report(
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
    kind: Optional[str] = Query(default="EXPENSE", alias="type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return per-category totals for the requested month and transaction type.

    type defaults to EXPENSE.  Only rows with a non-null category_id are included.
    Results are sorted descending by total.
    """
    now = datetime.now(timezone.utc)
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    tx_type = (kind or "EXPENSE").upper()
    month_start, month_end = _month_bounds(year, month)

    rows = (
        db.query(
            Transaction.category_id.label("category_id"),
            Category.name.label("category_name"),
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Category.id == Transaction.category_id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == tx_type,
            Transaction.date >= month_start,
            Transaction.date < month_end,
            Transaction.category_id.isnot(None),
        )
        .group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    grand_total = sum(r.total for r in rows) if rows else Decimal("0")

    return [
        CategoryReport(
            category_id=r.category_id,
            category_name=r.category_name,
            total=r.total,
            percentage=(float(r.total / grand_total * 100) if grand_total > 0 else 0.0),
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /reports/by-entity
# ---------------------------------------------------------------------------


@router.get("/by-entity", response_model=list[EntityReport])
def get_by_entity_report(  # pylint: disable=too-many-locals
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return per-bank-entity income / expense totals for the requested month.

    Income is credited to an entity when the destination account (to_account_id)
    belongs to that entity.  Expense / transfer is debited from an entity when
    the source account (from_account_id) belongs to that entity.

    Only entities that have at least one transaction that month are returned.
    """
    now = datetime.now(timezone.utc)
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    month_start, month_end = _month_bounds(year, month)

    # Subquery alias helpers — we need BankAccount twice (to/from).
    to_account_alias = BankAccount.__table__.alias("to_acct")
    from_account_alias = BankAccount.__table__.alias("from_acct")

    # --- Credits: INCOME transactions where to_account → bank entity ---
    credits_rows = (
        db.query(
            BankEntity.id.label("entity_id"),
            BankEntity.name.label("entity_name"),
            func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total_income"),
        )
        .join(to_account_alias, to_account_alias.c.id == Transaction.to_account_id)
        .join(BankEntity, BankEntity.id == to_account_alias.c.bank_entity_id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "INCOME",
            Transaction.to_account_id.isnot(None),
            Transaction.date >= month_start,
            Transaction.date < month_end,
        )
        .group_by(BankEntity.id, BankEntity.name)
        .all()
    )
    income_by_entity = {r.entity_id: (r.entity_name, r.total_income) for r in credits_rows}

    # --- Debits: EXPENSE or TRANSFER from_account → bank entity ---
    debits_rows = (
        db.query(
            BankEntity.id.label("entity_id"),
            BankEntity.name.label("entity_name"),
            func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total_expense"),
        )
        .join(from_account_alias, from_account_alias.c.id == Transaction.from_account_id)
        .join(BankEntity, BankEntity.id == from_account_alias.c.bank_entity_id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type.in_(["EXPENSE", "TRANSFER"]),
            Transaction.from_account_id.isnot(None),
            Transaction.date >= month_start,
            Transaction.date < month_end,
        )
        .group_by(BankEntity.id, BankEntity.name)
        .all()
    )
    expense_by_entity = {r.entity_id: (r.entity_name, r.total_expense) for r in debits_rows}

    # Merge the two dicts — include every entity that appears in either set.
    all_entity_ids = set(income_by_entity) | set(expense_by_entity)

    results = []
    for entity_id in all_entity_ids:
        entity_name = (
            income_by_entity.get(entity_id, (None, None))[0] or expense_by_entity.get(entity_id, (None, None))[0]
        )
        total_income = income_by_entity.get(entity_id, (None, Decimal("0")))[1]
        total_expense = expense_by_entity.get(entity_id, (None, Decimal("0")))[1]
        results.append(
            EntityReport(
                entity_id=entity_id,
                entity_name=entity_name,
                total_income=total_income,
                total_expense=total_expense,
                net=total_income - total_expense,
            )
        )

    # Sort by net descending for a consistent, useful ordering.
    results.sort(key=lambda r: r.net, reverse=True)
    return results
