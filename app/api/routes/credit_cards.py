# app\api\routes\credit_card.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.credit_card import CreditCard
from app.models.transaction import Transaction
from app.schemas.credit_card import (
    CreditCardCreate,
    CreditCardUpdate,
    CreditCardResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/credit-cards", tags=["Credit Cards"])


def _compute_used_amount(db: Session, card: CreditCard) -> float:
    """Compute used credit = SUM of EXPENSE transactions charged to this card."""
    result = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0))
        .filter(
            Transaction.from_credit_card_id == card.id,
            Transaction.type == "EXPENSE",
        )
        .scalar()
    )
    return float(result)


def _to_response(db: Session, card: CreditCard) -> CreditCardResponse:
    """Convert ORM object to response schema with computed used_amount."""
    return CreditCardResponse(
        id=card.id,
        name=card.name,
        credit_limit=card.credit_limit,
        brand=card.brand,
        closing_day=card.closing_day,
        due_day=card.due_day,
        interest_rate=card.interest_rate,
        used_amount=_compute_used_amount(db, card),
        currency_id=card.currency_id,
        currency=card.currency,
        bank_entity_id=card.bank_entity_id,
        bank_entity=card.bank_entity,
        user_id=card.user_id,
    )


# GET CREDIT CARDS
@router.get("", response_model=list[CreditCardResponse])
def get_credit_cards(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cards = (
        db.query(CreditCard)
        .options(
            joinedload(CreditCard.bank_entity),
            joinedload(CreditCard.currency),
        )
        .filter(CreditCard.user_id == current_user.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [_to_response(db, c) for c in cards]


# CREATE CREDIT CARD
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

    return _to_response(db, new_card)


# UPDATE CREDIT CARD
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

    if card.name is not None:
        existing.name = card.name
    if card.credit_limit is not None:
        existing.credit_limit = card.credit_limit
    if card.brand is not None:
        existing.brand = card.brand
    if card.closing_day is not None:
        existing.closing_day = card.closing_day
    if card.due_day is not None:
        existing.due_day = card.due_day
    if card.interest_rate is not None:
        existing.interest_rate = card.interest_rate
    if card.currency_id is not None:
        existing.currency_id = card.currency_id
    if card.bank_entity_id is not None:
        existing.bank_entity_id = card.bank_entity_id

    db.commit()
    db.refresh(existing)

    _ = existing.bank_entity
    _ = existing.currency

    return _to_response(db, existing)


# DELETE CREDIT CARD
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
