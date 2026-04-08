"""app/models/category.py"""

from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base


class Category(Base):
    """Modelo de categoría para ingresos y gastos."""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    type = Column(
        Enum("INCOME", "EXPENSE", name="category_type_enum"),
        nullable=False,
    )

    icon = Column(String(50), nullable=True)
    color = Column(String(6), nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Relaciones
    user = relationship("User", backref="categories")
    transactions = relationship("Transaction", back_populates="category")
    budget = relationship("Budget", back_populates="category", uselist=False)

    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete")
