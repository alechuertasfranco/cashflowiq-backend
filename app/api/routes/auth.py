# app/api/routes/auth.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import verify_firebase_token
from app.db.session import SessionLocal
from app.models.user import User

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/sync-user")
def sync_user(
    user_data=Depends(verify_firebase_token),
    db: Session = Depends(get_db),
):
    firebase_uid = user_data["uid"]
    email = user_data.get("email")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        user = User(firebase_uid=firebase_uid, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    return {"id": user.id}
