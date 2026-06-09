# app/models/recurring_transaction.py

from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum, DateTime, Boolean, Date
from app.db.base import Base


class RecurringTransaction(Base):
    __tablename__ = "recurring_transactions"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    amount = Column(Numeric(14, 2), nullable=True)

    type = Column(
        Enum("INCOME", "EXPENSE", name="recurring_type_enum"),
        nullable=False,
    )

    frequency = Column(
        Enum("DAILY", "WEEKLY", "MONTHLY", "YEARLY", name="frequency_enum"),
        nullable=False,
    )

    next_execution_date = Column(DateTime, nullable=False)

    # Optional end date — if set and next_execution_date would exceed it, rule is deactivated
    end_date = Column(Date, nullable=True)

    # Whether the rule is still active (False once end_date is passed or manually deactivated)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=True)

    # Currency of the generated transactions — derived from the linked account/card if omitted
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=True)

    notification_days_before = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relaciones
    category = relationship("Category")
    user = relationship("User", backref="recurring_transactions")
    currency = relationship("Currency")
