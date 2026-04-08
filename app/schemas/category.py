"""app/schemas/category.py"""

from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.budget import BudgetResponse


class CategoryBase(BaseModel):
    """Base schema for category creation and update."""

    name: str
    type: str  # INCOME | EXPENSE
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: Optional[str] = None
    type: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    """
    Category response enriched with:
    - children (subcategorías)
    - budget (presupuesto mensual)
    """

    id: int
    name: str
    type: str
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None
    user_id: int

    budget: Optional[BudgetResponse] = None

    children: List["CategoryResponse"] = Field(default_factory=list)

    class Config:
        """Pydantic configuration for CategoryResponse."""

        from_attributes = True


CategoryResponse.model_rebuild()
