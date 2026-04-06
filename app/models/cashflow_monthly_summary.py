# app/models/cashflow_monthly_summary.py

from sqlalchemy import Column, Integer, Numeric, ForeignKey
from app.db.base import Base


class CashflowMonthlySummary(Base):
    __tablename__ = "cashflow_monthly_summaries"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    total_income = Column(Numeric(14, 2), nullable=False)
    total_expense = Column(Numeric(14, 2), nullable=False)

    total_fixed_expense = Column(Numeric(14, 2), nullable=False)
    total_variable_expense = Column(Numeric(14, 2), nullable=False)

    savings = Column(Numeric(14, 2), nullable=False)
    savings_rate = Column(Numeric(5, 2), nullable=False)
