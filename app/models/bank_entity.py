# app/models/bank_entity.py

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class BankEntity(Base):
    __tablename__ = "bank_entities"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)

    name = Column(String(255), nullable=False)
    code = Column(String(4), nullable=False)
    color = Column(String(6), nullable=True)

    user = relationship("User", back_populates="bank_entities")
    accounts = relationship("BankAccount", back_populates="bank_entity")
    credit_cards = relationship("CreditCard", back_populates="bank_entity")
    investment_funds = relationship(
        "InvestmentFund", back_populates="bank_entity")
