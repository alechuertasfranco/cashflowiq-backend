# app/schemas/contact.py

from typing import Optional
from pydantic import BaseModel


class ContactCreate(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class ContactResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True
