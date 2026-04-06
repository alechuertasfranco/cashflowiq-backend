from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies.current_user import get_current_user, get_db
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["Categories"])


# 📥 GET /categories?type=INCOME
@router.get("", response_model=List[CategoryResponse])
def get_categories(
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Category).filter(Category.user_id == current_user.id)

    if type:
        query = query.filter(Category.type == type.upper())

    categories = query.order_by(Category.id.desc()).all()

    return categories


# 📥 POST /categories
@router.post("", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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
    current_user=Depends(get_current_user),
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == current_user.id)
        .first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if data.name is not None:
        category.name = data.name

    if data.type is not None:
        if data.type.upper() not in ["INCOME", "EXPENSE"]:
            raise HTTPException(
                status_code=400, detail="Invalid category type")
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
    current_user=Depends(get_current_user),
):
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.user_id == current_user.id)
        .first()
    )

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(category)
    db.commit()

    return {"message": "Category deleted successfully"}
