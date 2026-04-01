# app\api\routes\currencies.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.dependencies.current_user import get_db
from app.models.currency import Currency
from app.schemas.currency import CurrencyResponse

router = APIRouter(prefix="/currencies", tags=["Currencies"])


@router.get("/", response_model=List[CurrencyResponse])
def get_currencies(db: Session = Depends(get_db)):
    currencies = db.query(Currency).order_by(Currency.code).all()
    return currencies
