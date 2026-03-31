# app\models\currency.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), nullable=False, unique=True)  # USD, PEN, EUR
    name = Column(String(50), nullable=False)  # Sol, Dollar, Euro
    symbol = Column(String(5), nullable=False)  # S/, $, €

    accounts = relationship("BankAccount", back_populates="currency")
