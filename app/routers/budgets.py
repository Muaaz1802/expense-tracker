from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.budgets import Budget
from app.models.expenses import Expense
from app.schemas.budget import BudgetCreate, BudgetOut, BudgetStatus, BudgetUpdate

router = APIRouter(tags=["budgets"])


@router.get("/", response_model=list[BudgetOut])
async def list_budgets(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Budget)
        .where(Budget.user_id == user.user_id)
        .options(selectinload(Budget.category))
    )
    return result.scalars().all()


@router.post("/", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def create_budget(
    payload: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    if payload.start_date > payload.end_date:
        raise HTTPException(
            status_code=400, detail="start_date cannot be after end_date"
        )

    budget = Budget(
        user_id=user.user_id,
        category_id=payload.category_id,
        amount=payload.amount,
        period=payload.period,
        start_date=payload.start_date,
        end_date=payload.end_date,
        alert_threshold=payload.alert_threshold,
    )

    db.add(budget)
    await db.commit()

    result = await db.execute(
        select(Budget)
        .where(Budget.budget_id == budget.budget_id)
        .options(selectinload(Budget.category))
    )
    return result.scalar_one()


@router.put("/{id}", response_model=BudgetOut)
async def update_budget(
    id: UUID,
    payload: BudgetUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Budget).where(
            Budget.budget_id == id,
            Budget.user_id == user.user_id,
        )
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "start_date" in update_data and "end_date" in update_data:
        if update_data["start_date"] > update_data["end_date"]:
            raise HTTPException(
                status_code=400, detail="start_date cannot be after end_date"
            )

    for field, value in update_data.items():
        setattr(budget, field, value)

    await db.commit()

    result = await db.execute(
        select(Budget)
        .where(Budget.budget_id == id)
        .options(selectinload(Budget.category))
    )
    return result.scalar_one()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Budget).where(
            Budget.budget_id == id,
            Budget.user_id == user.user_id,
        )
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    await db.delete(budget)
    await db.commit()


@router.get("/{id}/status", response_model=BudgetStatus)
async def get_budget_status(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    result = await db.execute(
        select(Budget).where(
            Budget.budget_id == id,
            Budget.user_id == user.user_id,
        )
    )
    budget = result.scalar_one_or_none()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    expense_query = select(func.coalesce(func.sum(Expense.amount), 0)).where(
        Expense.user_id == user.user_id,
        Expense.expense_date >= budget.start_date,  # ← fixed
        Expense.expense_date <= budget.end_date,  # ← fixed
    )

    if budget.category_id:
        expense_query = expense_query.where(Expense.category_id == budget.category_id)

    spent_result = await db.execute(expense_query)
    spent = spent_result.scalar_one()

    spent = Decimal(spent or 0)
    remaining = budget.amount - spent
    percentage_used = float((spent / budget.amount) * 100 if budget.amount > 0 else 0)

    return BudgetStatus(
        budget_id=budget.budget_id,
        spent=spent,
        remaining=remaining,
        percentage_used=percentage_used,
    )
