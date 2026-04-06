# app/models/credit_card.py

from sqlalchemy import Column, Integer, String, Numeric, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class CreditCard(Base):
    __tablename__ = "credit_cards"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    credit_limit = Column(Numeric(12, 2), nullable=False)

    brand = Column(
        Enum("VISA", "MASTERCARD", "AMEX", "DISCOVER",
             "DINERS", name="card_brand_enum"),
        nullable=False,
    )

    closing_day = Column(Integer, nullable=False)
    due_day = Column(Integer, nullable=False)

    interest_rate = Column(Numeric(5, 2), nullable=True)

    currency_id = Column(Integer, ForeignKey(
        "currencies.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    bank_entity_id = Column(Integer, ForeignKey(
        "bank_entities.id"), nullable=False, index=True)

    user = relationship("User", back_populates="credit_cards")
    bank_entity = relationship("BankEntity", back_populates="credit_cards")
    currency = relationship("Currency")
