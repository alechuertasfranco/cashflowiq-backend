# app\models\user.py

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)

    bank_accounts = relationship("BankAccount", back_populates="user")
    bank_entities = relationship("BankEntity", back_populates="user")
    credit_cards = relationship("CreditCard", back_populates="user")
    investment_funds = relationship("InvestmentFund", back_populates="user")
