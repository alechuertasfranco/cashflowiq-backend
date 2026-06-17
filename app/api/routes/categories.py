"""app/api/routes/categories.py"""

from datetime import datetime

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, extract
from sqlalchemy.orm import Session, joinedload

from app.dependencies.current_user import get_current_user, get_db

from app.models.transaction import Transaction
from app.models.category import Category
from app.models.budget import Budget
from app.models.user import User
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


# 📥 GET /categories?type=INCOME
@router.get("", response_model=List[CategoryResponse])
def get_categories(
    category_type: Optional[str] = Query(None, alias="type"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve categories for the current user, optionally filtered by type."""
    query = db.query(Category).filter(Category.user_id == current_user.id)

    if category_type:
        query = query.filter(Category.type == category_type.upper())

    categories = query.order_by(Category.id.desc()).offset(offset).limit(limit).all()

    return categories


@router.get("/with-children", response_model=List[CategoryResponse])
def get_categories_with_children(
    category_type: Optional[str] = Query(None, alias="type"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return parent categories with:
    - children
    - budget (if exists)
    - spent (calculated for current month)
    """

    now = datetime.utcnow()

    query = db.query(Category).filter(Category.user_id == current_user.id, Category.parent_id.is_(None))

    if category_type:
        query = query.filter(Category.type == category_type.upper())

    categories = (
        query.options(joinedload(Category.children), joinedload(Category.budget).joinedload(Budget.currency))
        .order_by(Category.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    def _build_spent_map(tx_type: str) -> dict:
        return {
            row[0]: row[1]
            for row in db.query(
                Transaction.category_id,
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .filter(
                Transaction.user_id == current_user.id,
                Transaction.type == tx_type,
                Transaction.category_id.isnot(None),
                extract("month", Transaction.date) == now.month,
                extract("year", Transaction.date) == now.year,
            )
            .group_by(Transaction.category_id)
            .all()
        }

    expense_spent_map = _build_spent_map("EXPENSE")
    income_spent_map = _build_spent_map("INCOME")

    def attach_budget(category):
        if isinstance(category.budget, list):
            category.budget = category.budget[0] if category.budget else None

        if category.budget:
            # Use the spent map matching the category type
            spent_map = income_spent_map if category.type == "INCOME" else expense_spent_map
            child_ids = [child.id for child in (category.children or [])]
            all_ids = [category.id] + child_ids
            category.budget.spent = sum(spent_map.get(cid, 0) for cid in all_ids)

        for child in category.children or []:
            attach_budget(child)

    for cat in categories:
        attach_budget(cat)

    return categories


# 📥 POST /categories
@router.post("", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new category for the current user."""
    # Validar tipo
    if data.type.upper() not in ["INCOME", "EXPENSE"]:
        raise HTTPException(status_code=400, detail="Invalid category type")

    category = Category(
        name=data.name,
        type=data.type.upper(),
        icon=data.icon,
        color=data.color,
        parent_id=data.parent_id,
        user_id=current_user.id,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


# ✏️ PUT /categories/{id}
@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing category for the current user."""
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if data.name is not None:
        category.name = data.name

    if data.type is not None:
        if data.type.upper() not in ["INCOME", "EXPENSE"]:
            raise HTTPException(status_code=400, detail="Invalid category type")
        category.type = data.type.upper()

    if data.icon is not None:
        category.icon = data.icon

    if data.color is not None:
        category.color = data.color

    if data.parent_id is not None:
        category.parent_id = data.parent_id

    db.commit()
    db.refresh(category)

    return category


# ❌ DELETE /categories/{id}
@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a category for the current user."""
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()

    return {"message": "Category deleted successfully"}
