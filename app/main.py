# app/main.py

import logging
from fastapi import FastAPI
from app.api.routes import auth
from app.api.routes import bank_accounts
from app.api.routes import bank_entities
from app.api.routes import currencies

# Configuracion global de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(bank_accounts.router)
app.include_router(currencies.router)
