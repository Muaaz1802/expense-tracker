from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class CategoryOut(BaseModel):
    category_id: UUID
    name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    is_default: bool

    class Config:
        from_attributes = True
