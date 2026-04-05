# app/models/investment_fund.py

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class InvestmentFund(Base):
    __tablename__ = "investment_funds"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    # Cuánto dinero invertiste
    invested_amount = Column(Numeric(14, 2), nullable=False)

    # Tipo de fondo (opcional pero útil para insights)
    fund_type = Column(String(50), nullable=True)
    # Ej: "Mutual Fund", "ETF", "Index Fund"

    # Relaciones
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bank_entity_id = Column(Integer, ForeignKey("bank_entities.id"), nullable=False)

    user = relationship("User", backref="investment_funds")
    bank_entity = relationship("BankEntity", back_populates="investment_funds")
    currency = relationship("Currency")
