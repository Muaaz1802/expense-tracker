from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_spent: Decimal
    avg_per_day: Decimal
    top_category: Optional[str]


class CategoryBreakdownItem(BaseModel):
    category: str
    total: Decimal
    percentage: float


class CategoryBreakdownResponse(BaseModel):
    items: List[CategoryBreakdownItem]


class MonthlyTrendItem(BaseModel):
    month: str
    total: Decimal


class MonthlyTrendResponse(BaseModel):
    items: List[MonthlyTrendItem]
