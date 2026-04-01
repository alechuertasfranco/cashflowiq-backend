# app\models\currency.py

from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base


class Currency(Base):
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)

    # ISO
    code = Column(String(3), nullable=False, unique=True)

    # Display
    name = Column(String(50), nullable=False)
    symbol = Column(String(5), nullable=False)
    flag = Column(String(5), nullable=True)

    # Config
    decimals = Column(Integer, nullable=False, server_default="2")

    # 💱 Base: PEN (recomendado)
    exchange_rate_to_base = Column(Numeric(18, 6), nullable=True)

    # Relaciones
    accounts = relationship("BankAccount", back_populates="currency")
