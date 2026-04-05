# app\api\routes\credit_card.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models.credit_card import CreditCard
from app.schemas.credit_card import (
    CreditCardCreate,
    CreditCardUpdate,
    CreditCardResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/credit-cards", tags=["Credit Cards"])


# 📥 GET CREDIT CARDS
@router.get("", response_model=list[CreditCardResponse])
def get_credit_cards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(CreditCard)
        .options(
            joinedload(CreditCard.bank_entity),
            joinedload(CreditCard.currency),
        )
        .filter(CreditCard.user_id == current_user.id)
        .all()
    )


# ➕ CREATE CREDIT CARD
@router.post("", response_model=CreditCardResponse)
def create_credit_card(
    card: CreditCardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_card = CreditCard(
        name=card.name,
        credit_limit=card.credit_limit,
        brand=card.brand,
        closing_day=card.closing_day,
        due_day=card.due_day,
        interest_rate=card.interest_rate,
        currency_id=card.currency_id,
        bank_entity_id=card.bank_entity_id,
        user_id=current_user.id,
    )

    db.add(new_card)
    db.commit()
    db.refresh(new_card)

    # cargar relaciones
    _ = new_card.bank_entity
    _ = new_card.currency

    return new_card


# ✏️ UPDATE CREDIT CARD
@router.put("/{card_id}", response_model=CreditCardResponse)
def update_credit_card(
    card_id: int,
    card: CreditCardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(CreditCard)
        .filter(
            CreditCard.id == card_id,
            CreditCard.user_id == current_user.id,
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Credit card not found")

    existing.name = card.name
    existing.credit_limit = card.credit_limit
    existing.brand = card.brand
    existing.closing_day = card.closing_day
    existing.due_day = card.due_day
    existing.interest_rate = card.interest_rate
    existing.currency_id = card.currency_id
    existing.bank_entity_id = card.bank_entity_id

    db.commit()
    db.refresh(existing)

    _ = existing.bank_entity
    _ = existing.currency

    return existing


# ❌ DELETE CREDIT CARD
@router.delete("/{card_id}")
def delete_credit_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(CreditCard)
        .filter(
            CreditCard.id == card_id,
            CreditCard.user_id == current_user.id,
        )
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Credit card not found")

    db.delete(existing)
    db.commit()

    return {"message": "Deleted successfully"}
