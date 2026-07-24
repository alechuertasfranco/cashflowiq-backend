# app/models/statement_import.py

from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base


class StatementImport(Base):
    """
    A single bank-statement import batch.

    Groups every Transaction created from one imported "estado de cuenta" so
    the whole batch can be listed in history and undone atomically. The
    reconciliation (dedup against already-registered movements) happens on the
    client before the confirmed lines are POSTed here.
    """

    __tablename__ = "statement_imports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=False, index=True)

    # Period this statement consolidates (e.g. year=2026, month=6).
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    filename = Column(String, nullable=False)
    bank = Column(String, nullable=True)  # detected bank tag, e.g. "interbank" / "bcp"
    imported_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User")
    account = relationship("BankAccount")
    transactions = relationship(
        "Transaction",
        back_populates="import_batch",
        cascade="all, delete-orphan",
    )
