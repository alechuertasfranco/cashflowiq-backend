from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Reemplaza con tu conexión real
SQLALCHEMY_DATABASE_URL = "postgresql://usuario:contraseña@localhost:5432/nombre_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
