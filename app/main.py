"""app/main.py"""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    contacts,
    transaction_splits,
    payment_sources,
    payment_services,
    vouchers,
)
from app.services.recurring_executor import start_daily_scheduler

# Configuracion global de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions and return a generic 500 response."""
    logger.exception("Unhandled exception for %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


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
app.include_router(contacts.router)
app.include_router(transaction_splits.router)
app.include_router(payment_sources.router)
app.include_router(payment_services.router)
app.include_router(vouchers.router)
