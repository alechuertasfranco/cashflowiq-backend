# app/models/split_settlement.py

from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class SplitSettlement(Base):
    __tablename__ = "split_settlements"

    id = Column(Integer, primary_key=True, index=True)

    split_id = Column(Integer, ForeignKey(
        "transaction_splits.id"), nullable=False)

    amount = Column(Numeric(14, 2), nullable=False)

    date = Column(DateTime, default=datetime.utcnow)

    # Opcional: link a transaction real (transferencia)
    transaction_id = Column(Integer, ForeignKey(
        "transactions.id"), nullable=True)

    split = relationship("TransactionSplit", backref="settlements")
