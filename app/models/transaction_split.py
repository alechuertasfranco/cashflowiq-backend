# app/models/transaction_split.py

from sqlalchemy import Column, Integer, Numeric, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base


class TransactionSplit(Base):
    __tablename__ = "transaction_splits"

    id = Column(Integer, primary_key=True, index=True)

    transaction_id = Column(Integer, ForeignKey(
        "transactions.id"), nullable=False)

    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)

    # Cuánto le corresponde a esa persona
    amount = Column(Numeric(14, 2), nullable=False)

    # Si ya te pagó
    is_settled = Column(Boolean, default=False)

    transaction = relationship("Transaction", backref="splits")
    contact = relationship("Contact")
