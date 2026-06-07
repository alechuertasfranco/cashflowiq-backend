# app/api/routes/contacts.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.contact import Contact
from app.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from app.dependencies.current_user import get_current_user, get_db
from app.models.user import User

router = APIRouter(prefix="/contacts", tags=["Contacts"])


# GET CONTACTS
@router.get("", response_model=list[ContactResponse])
def list_contacts(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Contact)
        .filter(Contact.user_id == current_user.id)
        .order_by(Contact.name)
        .offset(offset)
        .limit(limit)
        .all()
    )


# CREATE CONTACT
@router.post("", response_model=ContactResponse)
def create_contact(
    data: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = Contact(
        user_id=current_user.id,
        name=data.name,
        email=data.email,
        phone=data.phone,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


# UPDATE CONTACT
@router.put("/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    data: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == current_user.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if data.name is not None:
        contact.name = data.name
    if data.email is not None:
        contact.email = data.email
    if data.phone is not None:
        contact.phone = data.phone

    db.commit()
    db.refresh(contact)
    return contact


# DELETE CONTACT
@router.delete("/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    contact = (
        db.query(Contact)
        .filter(Contact.id == contact_id, Contact.user_id == current_user.id)
        .first()
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return {"message": "Deleted successfully"}
