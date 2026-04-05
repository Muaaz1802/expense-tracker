from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    OTHER = "other"


class Expense(Base):
    __tablename__ = "expenses"

    expense_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.category_id"), nullable=False
    )
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    title = Column(String(255), nullable=False)
    description = Column(Text)
    expense_date: Mapped[datetime] = mapped_column(
        Date,
        nullable=False,
    )
    payment_method = Column(
        SQLEnum(PaymentMethod),
    )
    tags = Column(ARRAY(String), nullable=False, server_default="{}")
    reciept_url = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="expenses")
    category = relationship("Category", back_populates="expenses")
