# app/models/bank_entity.py

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class BankEntity(Base):
    __tablename__ = "bank_entities"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    color = Column(String(6), nullable=True)  # HEX sin '#'

    user = relationship("User", backref="bank_entities")
    accounts = relationship("BankAccount", back_populates="bank_entity")
