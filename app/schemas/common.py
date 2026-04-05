from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from .expense import PaymentMethod


class PaginationQuery(BaseModel):
    page: int = 1
    page_size: int = 10


class ExpenseFilter(BaseModel):
    start_date: Optional[date]
    end_date: Optional[date]
    category_id: Optional[UUID]
    payment_method: Optional[PaymentMethod]
    min_amount: Optional[Decimal]
    max_amount: Optional[Decimal]
    search: Optional[str]
