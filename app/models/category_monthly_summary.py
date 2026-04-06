# app/models/category_monthly_summary.py

from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class CategoryMonthlySummary(Base):
    __tablename__ = "category_monthly_summaries"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    total_amount = Column(Numeric(14, 2), nullable=False)

    # Opcional: separación por tipo
    total_income = Column(Numeric(14, 2), nullable=False)
    total_expense = Column(Numeric(14, 2), nullable=False)

    transaction_count = Column(Integer, nullable=False)

    user = relationship("User")
    category = relationship("Category")
