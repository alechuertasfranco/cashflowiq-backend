# app/db/init_db.py
from app.db.base import Base
from app.db.session import engine

# Importa modelos aquí para registrar las tablas en metadata
from app.models import user  # ❌ solo importa módulos, no clases individuales

Base.metadata.create_all(bind=engine)
