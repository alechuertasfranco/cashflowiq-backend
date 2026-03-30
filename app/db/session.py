# app/db/session.py

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Construir la URL codificando la contraseña correctamente
_password = quote_plus(os.getenv("POSTGRES_PASSWORD", ""))
_user = os.getenv("POSTGRES_USER", "postgres")
_host = os.getenv("POSTGRES_HOST", "localhost")
_port = os.getenv("POSTGRES_PORT", "5432")
_db = os.getenv("POSTGRES_DB", "cashflowiq")

DATABASE_URL = f"postgresql+psycopg2://{_user}:{_password}@{_host}:{_port}/{_db}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
