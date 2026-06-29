# app/api/routes/payment_services.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.payment_service import PaymentService
from app.schemas.payment_service import (
    PaymentServiceCreate,
    PaymentServiceUpdate,
    PaymentServiceResponse,
)
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/payment-services", tags=["Payment Services"])


@router.get("", response_model=list[PaymentServiceResponse])
def get_payment_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(PaymentService)
        .filter(PaymentService.user_id == current_user.id)
        .all()
    )


@router.post("", response_model=PaymentServiceResponse)
def create_payment_service(
    payload: PaymentServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PaymentService(
        user_id=current_user.id,
        name=payload.name,
        service_type=payload.service_type,
        account_id=payload.account_id,
        credit_card_id=payload.credit_card_id,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/{service_id}", response_model=PaymentServiceResponse)
def update_payment_service(
    service_id: int,
    payload: PaymentServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(PaymentService)
        .filter(
            PaymentService.id == service_id,
            PaymentService.user_id == current_user.id,
        )
        .first()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Payment service not found")

    if payload.name is not None:
        existing.name = payload.name
    if payload.service_type is not None:
        existing.service_type = payload.service_type
    if payload.account_id is not None:
        existing.account_id = payload.account_id
    if payload.credit_card_id is not None:
        existing.credit_card_id = payload.credit_card_id

    db.commit()
    db.refresh(existing)
    return existing


@router.delete("/{service_id}")
def delete_payment_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(PaymentService)
        .filter(
            PaymentService.id == service_id,
            PaymentService.user_id == current_user.id,
        )
        .first()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Payment service not found")

    db.delete(existing)
    db.commit()
    return {"message": "Deleted successfully"}
