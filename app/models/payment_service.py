from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class PaymentService(Base):
    __tablename__ = "payment_services"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    service_type = Column(String, nullable=False, default="generic")
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
    credit_card_id = Column(Integer, ForeignKey("credit_cards.id"), nullable=True)

    user = relationship("User", back_populates="payment_services")
    account = relationship("BankAccount")
    credit_card = relationship("CreditCard")
