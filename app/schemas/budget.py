from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, conint

from .category import CategoryOut


class Period(str, Enum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    YEARLY = "yearly"


class BudgetCreate(BaseModel):
    category_id: Optional[UUID]
    amount: Decimal
    period: Period
    start_date: date
    end_date: date
    alert_threshold: conint(ge=1, le=100)


class BudgetUpdate(BaseModel):
    category_id: Optional[UUID]
    amount: Optional[Decimal]
    period: Optional[Period]
    start_date: Optional[date]
    end_date: Optional[date]
    alert_threshold: Optional[conint(ge=1, le=100)]


class BudgetOut(BaseModel):
    budget_id: UUID
    category: Optional[CategoryOut]
    amount: Decimal
    period: Period
    start_date: date
    end_date: date
    alert_threshold: int
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetStatus(BaseModel):
    budget_id: UUID
    spent: Decimal
    remaining: Decimal
    percentage_used: float
