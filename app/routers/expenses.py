from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.categories import Category
from app.models.expenses import Expense
from app.models.users import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseOut,
    ExpensePartialUpdate,
    ExpenseUpdate,
    PaginatedExpenseResponse,
    PaymentMethod,
)
from app.services.users import get_current_user

router = APIRouter(tags=["expenses"])


@router.get("/", response_model=PaginatedExpenseResponse)
async def get_expenses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, le=100),
    category_id: Optional[UUID] = None,
    payment_method: Optional[PaymentMethod] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    sort_by: str = "expense_date",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Expense).where(Expense.user_id == current_user.user_id)

    if category_id:
        query = query.where(Expense.category_id == category_id)

    if payment_method:
        query = query.where(Expense.payment_method == payment_method)

    if start_date:
        query = query.where(Expense.expense_date >= start_date)

    if end_date:
        query = query.where(Expense.expense_date <= end_date)

    if min_amount:
        query = query.where(Expense.amount >= min_amount)

    if max_amount:
        query = query.where(Expense.amount <= max_amount)

    allowed_sort_fields = {"expense_date", "amount", "created_at"}
    sort_column = Expense.expense_date

    if sort_by in allowed_sort_fields:
        sort_column = getattr(Expense, sort_by)

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (page - 1) * page_size
    paginated_query = (
        query.options(selectinload(Expense.category)).offset(offset).limit(page_size)
    )

    result = await db.execute(paginated_query)
    expenses = result.scalars().all()

    count_query = (
        select(func.count())
        .select_from(Expense)
        .where(Expense.user_id == current_user.user_id)
    )

    if category_id:
        count_query = count_query.where(Expense.category_id == category_id)

    if payment_method:
        count_query = count_query.where(Expense.payment_method == payment_method)

    if start_date:
        count_query = count_query.where(Expense.expense_date >= start_date)

    if end_date:
        count_query = count_query.where(Expense.expense_date <= end_date)

    if min_amount:
        count_query = count_query.where(Expense.amount >= min_amount)

    if max_amount:
        count_query = count_query.where(Expense.amount <= max_amount)

    total = (await db.execute(count_query)).scalar_one()

    return {
        "items": expenses,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("/", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    new_expense: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        expense = Expense(
            user_id=current_user.user_id,
            category_id=new_expense.category_id,
            amount=new_expense.amount,
            currency=new_expense.currency,
            title=new_expense.title,
            description=new_expense.description,
            expense_date=new_expense.expense_date,
            payment_method=new_expense.payment_method,
            tags=new_expense.tags or [],
        )

        db.add(expense)
        await db.commit()

        # 🔴 REQUIRED: reload with relationship
        result = await db.execute(
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.expense_id == expense.expense_id)
        )
        expense = result.scalar_one()

        return expense

    except Exception:
        await db.rollback()
        raise


@router.get("/{expense_id}", response_model=ExpenseOut)
async def get_expense(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(
            Expense.expense_id == expense_id,
            Expense.user_id == current_user.user_id,
        )
    )

    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    return expense


@router.put("/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: UUID,
    updated_expense: ExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(
            Expense.expense_id == expense_id,
            Expense.user_id == current_user.user_id,
        )
    )

    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    expense.category_id = updated_expense.category_id
    expense.amount = updated_expense.amount
    expense.currency = updated_expense.currency
    expense.title = updated_expense.title
    expense.description = updated_expense.description
    expense.expense_date = updated_expense.expense_date
    expense.payment_method = updated_expense.payment_method
    expense.tags = updated_expense.tags or []

    try:
        await db.commit()
        await db.refresh(expense)
        return expense

    except Exception:
        await db.rollback()
        raise


@router.patch("/{expense_id}", response_model=ExpenseOut)
async def partial_update_expense(
    expense_id: UUID,
    updated_fields: ExpensePartialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(
            Expense.expense_id == expense_id,
            Expense.user_id == current_user.user_id,
        )
    )

    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    update_data = updated_fields.model_dump(exclude_unset=True)

    # category validation
    if "category_id" in update_data:
        result = await db.execute(
            select(Category).where(
                Category.category_id == update_data["category_id"],
                Category.user_id == current_user.user_id,
            )
        )
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    # tags normalization
    if "tags" in update_data:
        update_data["tags"] = update_data["tags"] or []

    for field, value in update_data.items():
        setattr(expense, field, value)

    try:
        await db.commit()
        await db.refresh(expense)
        return expense

    except Exception:
        await db.rollback()
        raise


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await db.execute(
            delete(Expense).where(
                Expense.expense_id == expense_id,
                Expense.user_id == current_user.user_id,
            )
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expense not found",
            )

        await db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except Exception:
        await db.rollback()
        raise


@router.get("/{expense_id}/status", response_model=ExpenseOut)
async def get_expense_status(
    expense_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(
            Expense.expense_id == expense_id,
            Expense.user_id == current_user.user_id,
        )
    )

    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found",
        )

    return expense
