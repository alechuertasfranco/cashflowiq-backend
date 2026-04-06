# app/models/budget.py

from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime
from app.db.base import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)

    amount = Column(Numeric(14, 2), nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Periodo
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    category = relationship("Category")
    user = relationship("User", backref="budgets")
