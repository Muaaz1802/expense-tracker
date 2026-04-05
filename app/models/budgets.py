from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Period(str, Enum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    YEARLY = "yearly"


class Budget(Base):
    __tablename__ = "budgets"

    budget_id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )
    category_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("categories.category_id"),
        nullable=True,
        index=True,
    )

    amount = Column(Numeric(12, 2), nullable=False)
    period = Column(SQLEnum(Period, name="peroid"), nullable=False)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    alert_threshold = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="budgets")
    category = relationship("Category", back_populates="budgets")
