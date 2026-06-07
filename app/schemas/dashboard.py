# app/schemas/dashboard.py

from decimal import Decimal
from typing import List
from pydantic import BaseModel


class AccountBalance(BaseModel):
    """Per-account running balance included in the dashboard summary."""

    id: int
    name: str
    currency_code: str
    balance: Decimal

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    """
    High-level financial summary for the current calendar month (UTC).

    total_income / total_expense cover only the current month.
    net_balance = total_income - total_expense.
    accounts contains every BankAccount with its all-time running balance.
    """

    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    accounts: List[AccountBalance]
