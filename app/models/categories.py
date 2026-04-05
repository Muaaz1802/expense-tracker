from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    name = Column(String(255), nullable=False)
    color = Column(String(7), nullable=True)
    icon = Column(String(255), nullable=True)

    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="categories")
    expenses = relationship(
        "Expense", back_populates="category", cascade="all, delete-orphan"
    )
    budgets = relationship(
        "Budget", back_populates="category", cascade="all, delete-orphan"
    )
