# app/models/entity_monthly_summary.py

from sqlalchemy import Column, Integer, Numeric, ForeignKey
from app.db.base import Base


class EntityMonthlySummary(Base):
    __tablename__ = "entity_monthly_summaries"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bank_entity_id = Column(Integer, ForeignKey(
        "bank_entities.id"), nullable=False)

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    total_balance = Column(Numeric(14, 2), nullable=False)
    total_debt = Column(Numeric(14, 2), nullable=False)

    total_income = Column(Numeric(14, 2), nullable=False)
    total_expense = Column(Numeric(14, 2), nullable=False)
