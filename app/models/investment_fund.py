# app/models/investment_fund.py

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class InvestmentFund(Base):
    __tablename__ = "investment_funds"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    invested_amount = Column(Numeric(14, 2), nullable=False)

    fund_type = Column(String(50), nullable=True)

    currency_id = Column(
        Integer, ForeignKey("currencies.id"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    bank_entity_id = Column(
        Integer, ForeignKey("bank_entities.id"), nullable=False, index=True
    )

    user = relationship("User", back_populates="investment_funds")
    bank_entity = relationship("BankEntity", back_populates="investment_funds")
    currency = relationship("Currency")
