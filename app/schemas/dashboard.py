# app/schemas/dashboard.py

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class AccountBalance(BaseModel):
    """Per-account running balance included in the dashboard summary."""

    id: int
    name: str
    currency_code: str
    bank_entity_code: str
    balance: Decimal

    class Config:
        from_attributes = True


class CreditCardBalance(BaseModel):
    """Per-card debt snapshot included in the dashboard summary."""

    id: int
    name: str
    brand: str
    currency_code: str
    bank_entity_code: str
    credit_limit: Decimal
    used_amount: Decimal
    closing_day: int
    due_day: int

    class Config:
        from_attributes = True


class DashboardSummary(BaseModel):
    """
    High-level financial summary for the current calendar month (UTC).

    total_income / total_expense cover only the current month.
    net_balance = total_income - total_expense.
    all_time_income / all_time_expense span the entire transaction history.
    accounts contains every BankAccount with its all-time running balance,
    sorted by balance descending.
    credit_cards contains every CreditCard with its current debt (used_amount).
    most_active_account_* identifies the account with the most transactions
    this month.
    """

    total_income: Decimal
    total_expense: Decimal
    net_balance: Decimal
    all_time_income: Decimal = Decimal("0")
    all_time_expense: Decimal = Decimal("0")
    accounts: List[AccountBalance]
    credit_cards: List[CreditCardBalance] = []
    most_active_account_id: Optional[int] = None
    most_active_account_name: Optional[str] = None
    most_active_account_tx_count: int = 0
