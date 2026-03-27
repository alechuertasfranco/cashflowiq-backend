# app/api/routes/auth.py

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth import verify_firebase_token
from app.db.session import SessionLocal
from app.models.user import User

router = APIRouter()

# Configuración de logger
logger = logging.getLogger(__name__)


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

    logger.info(f"[REQUEST] /sync-user llamado")
    logger.info(f"[TOKEN] uid={firebase_uid}, email={email}")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    if not user:
        logger.info("[SYNC USER] Usuario no existe, creando...")
        user = User(firebase_uid=firebase_uid, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        logger.info("[SYNC USER] Usuario ya existe")

    logger.info(f"[RESPONSE] user_id={user.id}")

    return {"id": user.id}
