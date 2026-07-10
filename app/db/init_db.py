# app/db/init_db.py

from app.db.base import Base
from app.db.session import engine

# Import for side effect only: registers every model's table on Base.metadata
# so create_all() below can see them, even though no names are used directly.
import app.models  # noqa: F401  pylint: disable=unused-import


def init_db():
    Base.metadata.create_all(bind=engine)
