# app/main.py

import logging
from fastapi import FastAPI
from app.api.routes import auth
from app.api.routes import bank_accounts

# Configuración global de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(bank_accounts.router)
