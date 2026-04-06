# app/models/monthly_balance.py

from sqlalchemy import Column, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class MonthlyBalance(Base):
    __tablename__ = "monthly_balances"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # Snapshot consolidado
    total_balance = Column(Numeric(14, 2), nullable=False)
    total_income = Column(Numeric(14, 2), nullable=False)
    total_expense = Column(Numeric(14, 2), nullable=False)

    # Opcional pero poderoso
    total_fixed_expense = Column(Numeric(14, 2), nullable=False)
    total_variable_expense = Column(Numeric(14, 2), nullable=False)

    user = relationship("User", backref="monthly_balances")
