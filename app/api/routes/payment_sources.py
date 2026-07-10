# app/api/routes/payment_sources.py

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.bank_account import BankAccount
from app.models.credit_card import CreditCard
from app.models.bank_entity import BankEntity
from app.models.transaction import Transaction
from app.schemas.bank_entity import BankEntityResponse
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/payment-sources", tags=["Payment Sources"])


class PaymentSourceResponse(BaseModel):
    type: str  # "account" or "credit_card"
    id: int
    name: str
    bank_entity: BankEntityResponse


@router.get("/most-used", response_model=list[PaymentSourceResponse])
def get_most_used_payment_sources(
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account_rows = (
        db.query(
            BankAccount.id,
            BankAccount.name,
            BankAccount.bank_entity_id,
            func.count(Transaction.id).label("usage_count"),  # pylint: disable=not-callable
        )
        .outerjoin(
            Transaction,
            (Transaction.from_account_id == BankAccount.id)
            | (Transaction.to_account_id == BankAccount.id),
        )
        .filter(BankAccount.user_id == current_user.id)
        .group_by(BankAccount.id, BankAccount.name, BankAccount.bank_entity_id)
        .all()
    )

    card_rows = (
        db.query(
            CreditCard.id,
            CreditCard.name,
            CreditCard.bank_entity_id,
            func.count(Transaction.id).label("usage_count"),  # pylint: disable=not-callable
        )
        .outerjoin(
            Transaction,
            (Transaction.from_credit_card_id == CreditCard.id)
            | (Transaction.to_credit_card_id == CreditCard.id),
        )
        .filter(CreditCard.user_id == current_user.id)
        .group_by(CreditCard.id, CreditCard.name, CreditCard.bank_entity_id)
        .all()
    )

    entity_ids = {row.bank_entity_id for row in account_rows} | {row.bank_entity_id for row in card_rows}
    entities = (
        {e.id: e for e in db.query(BankEntity).filter(BankEntity.id.in_(entity_ids)).all()}
        if entity_ids
        else {}
    )

    sources: list[dict] = []
    for row in account_rows:
        entity = entities.get(row.bank_entity_id)
        if entity:
            sources.append({"type": "account", "id": row.id, "name": row.name, "entity": entity, "usage_count": row.usage_count})

    for row in card_rows:
        entity = entities.get(row.bank_entity_id)
        if entity:
            sources.append({"type": "credit_card", "id": row.id, "name": row.name, "entity": entity, "usage_count": row.usage_count})

    sources.sort(key=lambda s: s["usage_count"], reverse=True)

    return [
        PaymentSourceResponse(
            type=s["type"],
            id=s["id"],
            name=s["name"],
            bank_entity=BankEntityResponse.model_validate(s["entity"]),
        )
        for s in sources[:limit]
    ]
