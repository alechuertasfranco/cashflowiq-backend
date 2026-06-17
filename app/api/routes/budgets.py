"""app/api/routes/budgets.py"""

from decimal import Decimal
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from app.dependencies.current_user import get_current_user, get_db
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetResponse

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post("", response_model=BudgetResponse)
def create_or_update_budget(
    data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create or update a monthly budget for a category.

    - Si ya existe un presupuesto para la categoría → se actualiza.
    - Si no existe → se crea.
    """

    budget = (
        db.query(Budget)
        .filter(
            Budget.category_id == data.category_id,
            Budget.user_id == current_user.id,
        )
        .first()
    )

    if budget:
        budget.amount = data.amount
    else:
        budget = Budget(
            amount=data.amount,
            currency_id=data.currency_id,
            category_id=data.category_id,
            user_id=current_user.id,
        )
        db.add(budget)

    db.commit()
    db.refresh(budget)

    return budget


@router.get("", response_model=list[BudgetResponse])
def get_budgets(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all budgets for the current user,
    incluyendo el gasto actual del mes.
    """

    now = datetime.utcnow()

    budgets = (
        db.query(Budget)
        .filter(Budget.user_id == current_user.id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Pre-load category type for each budgeted category
    cat_ids = [b.category_id for b in budgets]
    category_type_map = {
        c.id: c.type
        for c in db.query(Category.id, Category.type)
        .filter(Category.id.in_(cat_ids))
        .all()
    }

    results = []

    for b in budgets:
        tx_type = category_type_map.get(b.category_id, "EXPENSE")
        child_ids = [
            c.id
            for c in db.query(Category.id)
            .filter(Category.parent_id == b.category_id, Category.user_id == current_user.id)
            .all()
        ]
        all_category_ids = [b.category_id] + child_ids
        spent = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.category_id.in_(all_category_ids),
                Transaction.user_id == current_user.id,
                Transaction.currency_id == b.currency_id,
                Transaction.type == tx_type,
                extract("month", Transaction.date) == now.month,
                extract("year", Transaction.date) == now.year,
            )
            .scalar()
        )

        results.append(
            BudgetResponse(
                id=b.id,
                amount=b.amount,
                category_id=b.category_id,
                user_id=b.user_id,
                spent=Decimal(spent),
                created_at=b.created_at,
            )
        )

    return results
