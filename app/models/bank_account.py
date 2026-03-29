# app/models/bank_account.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    initial_amount = Column(Float, nullable=False, default=0)
    currency = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bank_entity_id = Column(Integer, ForeignKey("bank_entities.id"), nullable=False)

    user = relationship("User", backref="bank_accounts")
    bank_entity = relationship("BankEntity", back_populates="accounts")
