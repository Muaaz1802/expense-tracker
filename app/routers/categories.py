from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.categories import Category
from app.models.expenses import Expense
from app.models.users import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.users import get_current_user

router = APIRouter(tags=["categories"])


@router.get("/", response_model=List[CategoryOut])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(
            Category.user_id == current_user.user_id  # both UUID now
        )
    )
    print("TOKEN USER:", current_user.user_id)
    categories = result.scalars().all()
    return categories


@router.post("/", response_model=CategoryOut)
async def create_category(
    category_create: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    name = category_create.name.strip().lower()

    result = await db.execute(
        select(Category).where(
            Category.user_id == current_user.user_id,
            Category.name == name,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    try:
        new_category = Category(
            user_id=current_user.user_id,
            name=name,
            color=category_create.color,
            icon=category_create.icon,
        )

        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)

        return new_category

    except Exception:
        await db.rollback()
        raise


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: UUID,
    category_update: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(
            Category.category_id == category_id,
            Category.user_id == current_user.user_id,
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    try:
        if category_update.name is not None:
            name = category_update.name.strip().lower()

            result = await db.execute(
                select(Category).where(
                    Category.user_id == current_user.user_id,
                    Category.name == name,
                    Category.category_id != category_id,
                )
            )
            if result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Category already exists")

            category.name = name

        if category_update.color is not None:
            category.color = category_update.color

        if category_update.icon is not None:
            category.icon = category_update.icon

        await db.commit()
        await db.refresh(category)

        return category

    except Exception:
        await db.rollback()
        raise


@router.delete("/{category_id}")
async def delete_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):

    # 1. Check category exists
    result = await db.execute(
        select(Category).where(
            Category.category_id == category_id,
            Category.user_id == current_user.user_id,
        )
    )
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # 2. Check if category is used
    result = await db.execute(select(Expense).where(Expense.category_id == category_id))
    expense = result.first()

    if expense:
        raise HTTPException(
            status_code=400,
            detail="Category has expenses. Delete or reassign them first.",
        )

    # 3. Safe delete
    await db.delete(category)
    await db.commit()

    return {"message": "Category deleted successfully"}
