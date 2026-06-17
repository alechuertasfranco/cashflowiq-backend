# app/dependencies/current_user.py

from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import verify_firebase_token
from app.db.session import SessionLocal
from app.models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    user_data: dict = Depends(verify_firebase_token),
    db: Session = Depends(get_db),
) -> User:
    firebase_uid = user_data["uid"]

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    return user
