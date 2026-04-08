"""app/models/budget.py"""

from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, UniqueConstraint
from app.db.base import Base


class Budget(Base):
    """
    Modelo de presupuesto mensual por categoría.

    Cada registro representa el monto mensual asignado a una categoría
    para un usuario. No se maneja período explícito ya que el presupuesto
    es recurrente cada mes.
    """

    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)

    amount = Column(Numeric(14, 2), nullable=False)

    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("category_id", "user_id", name="uq_budget_category_user"),)

    # Relaciones
    currency = relationship("Currency", backref="budget", uselist=False)
    category = relationship("Category", back_populates="budget")
    user = relationship("User", backref="budgets")
