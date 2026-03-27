from app.db.base import Base
from app.db.session import engine

# Importar modelos para registrarlos en Base.metadata
from app.models import user  # solo importa los módulos que definen modelos


# Crear todas las tablas (opcional si vas a usar solo Alembic)
def init_db():
    Base.metadata.create_all(bind=engine)
