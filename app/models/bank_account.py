# app/models/bank_account.py

from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    initial_amount = Column(Numeric(12, 2), nullable=False, default=0)

    currency_id = Column(Integer, ForeignKey(
        "currencies.id"), nullable=False, index=True)

    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    bank_entity_id = Column(Integer, ForeignKey(
        "bank_entities.id"), nullable=False, index=True)

    user = relationship("User", back_populates="bank_accounts")
    bank_entity = relationship("BankEntity", back_populates="accounts")
    currency = relationship("Currency", back_populates="accounts")
