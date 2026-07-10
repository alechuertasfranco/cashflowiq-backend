import os
import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

# 📌 Obtener ruta absoluta del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/
ROOT_DIR = os.path.dirname(BASE_DIR)  # raiz del proyecto

cred_path = os.path.join(
    BASE_DIR,
    "core",
    "config",
    "serviceAccountKey.json",
)

# Inicializar Firebase una sola vez
try:
    firebase_admin.get_app()
except ValueError:
    if not os.path.exists(cred_path):
        # Not actually caused by the ValueError above (that just means no
        # Firebase app is initialized yet) — this is an unrelated config
        # problem, so it's raised fresh rather than chained.
        raise RuntimeError(f"No se encontro serviceAccountKey.json en: {cred_path}") from None

    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)


async def verify_firebase_token(
    auth_credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        token = auth_credentials.credentials
        decoded_token = auth.verify_id_token(token)
        return decoded_token  # uid, email, etc.
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
        ) from exc
