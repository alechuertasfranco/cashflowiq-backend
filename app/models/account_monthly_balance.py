# app/models/account_monthly_balance.py

from sqlalchemy import Column, Integer, Numeric, ForeignKey
from app.db.base import Base


class AccountMonthlyBalance(Base):
    __tablename__ = "account_monthly_balances"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )

    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
    credit_card_id = Column(
        Integer, ForeignKey("credit_cards.id"), nullable=True
    )
    investment_fund_id = Column(
        Integer, ForeignKey("investment_funds.id"), nullable=True
    )

    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    initial_balance = Column(Numeric(14, 2), nullable=False)
    final_balance = Column(Numeric(14, 2), nullable=False)

    total_inflow = Column(Numeric(14, 2), nullable=False)
    total_outflow = Column(Numeric(14, 2), nullable=False)
