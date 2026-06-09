from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class InvestmentFundSnapshot(Base):
    __tablename__ = "investment_fund_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    investment_fund_id = Column(
        Integer,
        ForeignKey("investment_funds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False)
    value = Column(Numeric(14, 2), nullable=False)

    fund = relationship("InvestmentFund", back_populates="snapshots")
