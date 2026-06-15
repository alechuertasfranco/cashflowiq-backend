# app/api/routes/reports.py

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case
from sqlalchemy.orm import Session, aliased

from app.dependencies.current_user import get_current_user, get_db
from app.models.bank_account import BankAccount
from app.models.bank_entity import BankEntity
from app.models.budget import Budget
from app.models.category import Category
from app.models.currency import Currency
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.reports import (
    BudgetVsActualItem,
    CashflowReport,
    CategoryReport,
    EntityReport,
    MonthlyTrendPoint,
)

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


@router.get("/cashflow", response_model=List[CashflowReport])
def get_cashflow_report(
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return cashflow summaries for the requested month, one entry per currency.

    Defaults to the current UTC year / month when omitted.
    """
    now = datetime.now(timezone.utc)
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    month_start, month_end = _month_bounds(year, month)

    rows = (
        db.query(
            Currency.id.label("currency_id"),
            Currency.code.label("currency_code"),
            Currency.symbol.label("currency_symbol"),
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
        .join(Currency, Currency.id == Transaction.currency_id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= month_start,
            Transaction.date < month_end,
        )
        .group_by(Currency.id, Currency.code, Currency.symbol)
        .all()
    )

    results = []
    for row in rows:
        total_income = row.total_income or Decimal("0")
        total_expense = row.total_expense or Decimal("0")
        fixed_expense = row.fixed_expense or Decimal("0")
        variable_expense = row.variable_expense or Decimal("0")

        if total_income > 0:
            savings_rate = float((total_income - total_expense) / total_income * 100)
        else:
            savings_rate = 0.0

        results.append(
            CashflowReport(
                year=year,
                month=month,
                currency_code=row.currency_code,
                currency_symbol=row.currency_symbol,
                total_income=total_income,
                total_expense=total_expense,
                fixed_expense=fixed_expense,
                variable_expense=variable_expense,
                savings_rate=savings_rate,
            )
        )

    return results


# ---------------------------------------------------------------------------
# GET /reports/by-category
# ---------------------------------------------------------------------------


@router.get("/by-category", response_model=List[CategoryReport])
def get_by_category_report(
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
    kind: Optional[str] = Query(default="EXPENSE", alias="type"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return per-category totals for the requested month and transaction type,
    grouped by currency.

    type defaults to EXPENSE.  Only rows with a non-null category_id are included.
    Results are sorted by currency code then descending total within each currency.
    Percentage is computed within each currency group.
    """
    now = datetime.now(timezone.utc)
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    tx_type = (kind or "EXPENSE").upper()
    month_start, month_end = _month_bounds(year, month)

    ParentCategory = aliased(Category)

    rows = (
        db.query(
            Transaction.category_id.label("category_id"),
            Category.name.label("category_name"),
            Category.parent_id.label("parent_category_id"),
            ParentCategory.name.label("parent_category_name"),
            Currency.code.label("currency_code"),
            Currency.symbol.label("currency_symbol"),
            func.sum(Transaction.amount).label("total"),
        )
        .join(Category, Category.id == Transaction.category_id)
        .outerjoin(ParentCategory, ParentCategory.id == Category.parent_id)
        .join(Currency, Currency.id == Transaction.currency_id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == tx_type,
            Transaction.date >= month_start,
            Transaction.date < month_end,
            Transaction.category_id.isnot(None),
        )
        .group_by(
            Currency.id, Currency.code, Currency.symbol,
            Transaction.category_id, Category.name, Category.parent_id,
            ParentCategory.name,
        )
        .order_by(Currency.code, func.sum(Transaction.amount).desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Compute per-currency grand totals so percentage is within each currency.
    currency_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for r in rows:
        currency_totals[r.currency_code] += r.total

    return [
        CategoryReport(
            category_id=r.category_id,
            category_name=r.category_name,
            parent_category_id=r.parent_category_id,
            parent_category_name=r.parent_category_name,
            currency_code=r.currency_code,
            currency_symbol=r.currency_symbol,
            total=r.total,
            percentage=(
                float(r.total / currency_totals[r.currency_code] * 100)
                if currency_totals[r.currency_code] > 0
                else 0.0
            ),
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /reports/by-entity
# ---------------------------------------------------------------------------


@router.get("/by-entity", response_model=List[EntityReport])
def get_by_entity_report(  # pylint: disable=too-many-locals
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return per-bank-entity income / expense totals for the requested month,
    grouped by currency.

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

    # --- Credits: INCOME transactions where to_account → bank entity, per currency ---
    credits_rows = (
        db.query(
            BankEntity.id.label("entity_id"),
            BankEntity.name.label("entity_name"),
            Currency.code.label("currency_code"),
            Currency.symbol.label("currency_symbol"),
            func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total_income"),
        )
        .join(to_account_alias, to_account_alias.c.id == Transaction.to_account_id)
        .join(BankEntity, BankEntity.id == to_account_alias.c.bank_entity_id)
        .join(Currency, Currency.id == Transaction.currency_id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "INCOME",
            Transaction.to_account_id.isnot(None),
            Transaction.date >= month_start,
            Transaction.date < month_end,
        )
        .group_by(BankEntity.id, BankEntity.name, Currency.id, Currency.code, Currency.symbol)
        .all()
    )
    # Key: (entity_id, currency_code)
    income_by_key: dict[tuple, dict] = {}
    for r in credits_rows:
        income_by_key[(r.entity_id, r.currency_code)] = {
            "entity_name": r.entity_name,
            "currency_code": r.currency_code,
            "currency_symbol": r.currency_symbol,
            "total_income": r.total_income,
        }

    # --- Debits: EXPENSE or TRANSFER from_account → bank entity, per currency ---
    debits_rows = (
        db.query(
            BankEntity.id.label("entity_id"),
            BankEntity.name.label("entity_name"),
            Currency.code.label("currency_code"),
            Currency.symbol.label("currency_symbol"),
            func.coalesce(func.sum(Transaction.amount), Decimal("0")).label("total_expense"),
        )
        .join(from_account_alias, from_account_alias.c.id == Transaction.from_account_id)
        .join(BankEntity, BankEntity.id == from_account_alias.c.bank_entity_id)
        .join(Currency, Currency.id == Transaction.currency_id)
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type.in_(["EXPENSE", "TRANSFER"]),
            Transaction.from_account_id.isnot(None),
            Transaction.date >= month_start,
            Transaction.date < month_end,
        )
        .group_by(BankEntity.id, BankEntity.name, Currency.id, Currency.code, Currency.symbol)
        .all()
    )
    expense_by_key: dict[tuple, dict] = {}
    for r in debits_rows:
        expense_by_key[(r.entity_id, r.currency_code)] = {
            "entity_name": r.entity_name,
            "currency_code": r.currency_code,
            "currency_symbol": r.currency_symbol,
            "total_expense": r.total_expense,
        }

    # Merge the two dicts — include every (entity, currency) combination.
    all_keys = set(income_by_key) | set(expense_by_key)

    results = []
    for key in all_keys:
        entity_id, currency_code = key
        income_data = income_by_key.get(key, {})
        expense_data = expense_by_key.get(key, {})

        entity_name = income_data.get("entity_name") or expense_data.get("entity_name")
        currency_symbol = income_data.get("currency_symbol") or expense_data.get("currency_symbol")
        total_income = income_data.get("total_income", Decimal("0"))
        total_expense = expense_data.get("total_expense", Decimal("0"))

        results.append(
            EntityReport(
                entity_id=entity_id,
                entity_name=entity_name,
                currency_code=currency_code,
                currency_symbol=currency_symbol,
                total_income=total_income,
                total_expense=total_expense,
                net=total_income - total_expense,
            )
        )

    # Sort by currency code then net descending for a consistent, useful ordering.
    results.sort(key=lambda r: (r.currency_code, -r.net))
    return results[offset: offset + limit]


# ---------------------------------------------------------------------------
# GET /reports/monthly-trend
# ---------------------------------------------------------------------------


@router.get("/monthly-trend", response_model=List[MonthlyTrendPoint])
def get_monthly_trend(
    months: int = Query(default=6, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return cashflow totals for the last N calendar months (default 6), newest last.
    One entry per (month, currency) pair that has at least one transaction.
    """
    now = datetime.now(timezone.utc)

    # Build the list of (year, month) tuples going back `months` steps from the
    # current month, oldest first.
    periods: list[tuple[int, int]] = []
    y, m = now.year, now.month
    for _ in range(months):
        periods.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    periods.reverse()  # oldest first → newest last

    results: list[MonthlyTrendPoint] = []

    for period_year, period_month in periods:
        period_start, period_end = _month_bounds(period_year, period_month)

        rows = (
            db.query(
                Currency.code.label("currency_code"),
                Currency.symbol.label("currency_symbol"),
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
            .join(Currency, Currency.id == Transaction.currency_id)
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.date >= period_start,
                Transaction.date < period_end,
            )
            .group_by(Currency.id, Currency.code, Currency.symbol)
            .all()
        )

        for row in rows:
            income = row.total_income or Decimal("0")
            expense = row.total_expense or Decimal("0")
            results.append(
                MonthlyTrendPoint(
                    year=period_year,
                    month=period_month,
                    currency_code=row.currency_code,
                    currency_symbol=row.currency_symbol,
                    total_income=income,
                    total_expense=expense,
                    net=income - expense,
                )
            )

    return results


# ---------------------------------------------------------------------------
# GET /reports/budget-vs-actual
# ---------------------------------------------------------------------------


@router.get("/budget-vs-actual", response_model=List[BudgetVsActualItem])
def get_budget_vs_actual(
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compare budgeted amounts against actual spending for the given month.

    Only categories with a budget defined are included.  Sub-category spending
    is rolled up into the parent budget when the budget is set at the parent level.
    """
    now = datetime.now(timezone.utc)
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    month_start, month_end = _month_bounds(year, month)

    ParentCategory = aliased(Category)

    # All budgets for this user with their category and currency details.
    budget_rows = (
        db.query(
            Budget.category_id.label("category_id"),
            Category.name.label("category_name"),
            Category.parent_id.label("parent_category_id"),
            ParentCategory.name.label("parent_category_name"),
            Budget.amount.label("budget_amount"),
            Currency.code.label("currency_code"),
            Currency.symbol.label("currency_symbol"),
        )
        .join(Category, Category.id == Budget.category_id)
        .outerjoin(ParentCategory, ParentCategory.id == Category.parent_id)
        .join(Currency, Currency.id == Budget.currency_id)
        .filter(Budget.user_id == current_user.id)
        .all()
    )

    if not budget_rows:
        return []

    # Pre-fetch child categories for each budgeted parent so we can roll up spending.
    budgeted_cat_ids = [r.category_id for r in budget_rows]
    children_rows = (
        db.query(Category.id, Category.parent_id)
        .filter(
            Category.parent_id.in_(budgeted_cat_ids),
            Category.user_id == current_user.id,
        )
        .all()
    )
    children_by_parent: dict[int, list[int]] = defaultdict(list)
    for child in children_rows:
        children_by_parent[child.parent_id].append(child.id)

    # Pre-fetch actual spending per category for this month.
    spending_rows = (
        db.query(
            Transaction.category_id.label("category_id"),
            func.sum(Transaction.amount).label("total"),
        )
        .filter(
            Transaction.user_id == current_user.id,
            Transaction.type == "EXPENSE",
            Transaction.date >= month_start,
            Transaction.date < month_end,
            Transaction.category_id.isnot(None),
        )
        .group_by(Transaction.category_id)
        .all()
    )
    spending_map: dict[int, Decimal] = {r.category_id: r.total for r in spending_rows}

    results: list[BudgetVsActualItem] = []
    for row in budget_rows:
        # Roll up: own spending + spending of direct children.
        all_cat_ids = [row.category_id] + children_by_parent.get(row.category_id, [])
        spent = sum((spending_map.get(cid, Decimal("0")) for cid in all_cat_ids), Decimal("0"))

        budget_amount = row.budget_amount or Decimal("0")
        percentage = float(spent / budget_amount * 100) if budget_amount > 0 else 0.0

        results.append(
            BudgetVsActualItem(
                category_id=row.category_id,
                category_name=row.category_name,
                parent_category_id=row.parent_category_id,
                parent_category_name=row.parent_category_name,
                currency_code=row.currency_code,
                currency_symbol=row.currency_symbol,
                budget_amount=budget_amount,
                spent_amount=spent,
                percentage_used=percentage,
            )
        )

    # Sort: over-budget first (highest % used), then alphabetically.
    results.sort(key=lambda r: (-r.percentage_used, r.category_name))
    return results
