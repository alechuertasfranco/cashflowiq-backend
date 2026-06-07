# app\api\routes\bank_entities.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.bank_entity import BankEntity
from app.schemas.bank_entity import (
    BankEntityCreate,
    BankEntityUpdate,
    BankEntityResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/bank-entities", tags=["Bank Entities"])


@router.get("", response_model=list[BankEntityResponse])
def get_entities(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entities = (
        db.query(BankEntity)
        .filter(BankEntity.user_id == current_user.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return entities


@router.post("", response_model=BankEntityResponse)
def create_entity(
    entity: BankEntityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_entity = BankEntity(
        name=entity.name, code=entity.code, color=entity.color, user_id=current_user.id
    )
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity


@router.put("/{entity_id}", response_model=BankEntityResponse)
def update_entity(
    entity_id: int,
    entity: BankEntityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(BankEntity)
        .filter(BankEntity.id == entity_id, BankEntity.user_id == current_user.id)
        .first()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Entity not found")

    existing.name = entity.name
    existing.code = entity.code
    existing.color = entity.color
    db.commit()
    db.refresh(existing)
    return existing


@router.delete("/{entity_id}")
def delete_entity(
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(BankEntity)
        .filter(BankEntity.id == entity_id, BankEntity.user_id == current_user.id)
        .first()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Entity not found")

    db.delete(existing)
    db.commit()
    return {"message": "Deleted successfully"}
