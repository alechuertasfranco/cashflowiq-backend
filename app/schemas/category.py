"""app/schemas/category.py"""

from typing import List
from typing import Optional
from pydantic import BaseModel, Field


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
    """Schema for updating a new category."""
    name: Optional[str] = None
    type: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    """Category response."""
    id: int
    name: str
    type: str
    icon: Optional[str]
    color: Optional[str]
    parent_id: Optional[int]
    user_id: int

    children: List["CategoryResponse"] = Field(default_factory=list)

    class Config:
        """"CategoryResponse - Config"""
        from_attributes = True


CategoryResponse.model_rebuild()
