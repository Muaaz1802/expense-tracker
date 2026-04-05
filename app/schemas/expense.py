from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.category import CategoryOut


class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    UPI = "upi"
    NET_BANKING = "net_banking"
    OTHER = "other"


class ExpenseCreate(BaseModel):
    category_id: UUID
    amount: Decimal
    currency: str = "INR"
    title: str
    description: Optional[str] = None
    expense_date: date
    payment_method: PaymentMethod
    tags: List[str] = Field(default_factory=list)


class ExpenseUpdate(BaseModel):
    category_id: UUID
    amount: Decimal
    currency: str
    title: str
    description: Optional[str] = None
    expense_date: date
    payment_method: PaymentMethod
    tags: List[str] = Field(default_factory=list)


class ExpensePartialUpdate(BaseModel):
    category_id: Optional[UUID] = None
    amount: Optional[Decimal] = None
    title: Optional[str] = None
    description: Optional[str] = None
    payment_method: Optional[PaymentMethod] = None
    tags: Optional[List[str]] = None


class ExpenseOut(BaseModel):
    expense_id: UUID
    category: CategoryOut
    amount: Decimal
    currency: str
    title: str
    description: Optional[str] = None
    expense_date: date
    payment_method: PaymentMethod
    tags: List[str] = Field(default_factory=list)
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedExpenseResponse(BaseModel):
    items: List[ExpenseOut]
    total: int
    page: int
    page_size: int
    pages: int
