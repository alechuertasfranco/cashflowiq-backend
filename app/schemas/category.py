# app/schemas/category.py

from typing import Optional
from pydantic import BaseModel


class CategoryBase(BaseModel):
    name: str
    type: str  # INCOME | EXPENSE
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    icon: Optional[str]
    color: Optional[str]
    parent_id: Optional[int]

    user_id: int

    class Config:
        from_attributes = True
