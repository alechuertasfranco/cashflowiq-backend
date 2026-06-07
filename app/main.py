"""app/main.py"""

import logging
from fastapi import FastAPI
from app.api.routes import (
    auth,
    bank_accounts,
    bank_entities,
    currencies,
    credit_cards,
    investment_funds,
    categories,
    budgets,
    transactions,
    dashboard,
    reports,
    recurring_transactions,
)
from app.services.recurring_executor import start_daily_scheduler

# Configuracion global de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI()


@app.on_event("startup")
def on_startup() -> None:
    """Start the background scheduler that fires due recurring transactions."""
    start_daily_scheduler()


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(bank_accounts.router)
app.include_router(bank_entities.router)
app.include_router(currencies.router)
app.include_router(credit_cards.router)
app.include_router(investment_funds.router)
app.include_router(categories.router)
app.include_router(budgets.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(reports.router)
app.include_router(recurring_transactions.router)
