import csv
import io
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.categories import Category
from app.models.expenses import Expense
from app.models.users import User
from app.services.users import get_current_user

router = APIRouter(tags=["reports"])


def _expense_filters(user_id, start: Optional[date], end: Optional[date]):
    filters = [Expense.user_id == user_id]
    if start:
        filters.append(Expense.expense_date >= start)
    if end:
        filters.append(Expense.expense_date <= end)
    return filters


# ── GET /summary ──────────────────────────────────────────────────────────────


@router.get("/summary")
async def get_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = _expense_filters(current_user.user_id, start_date, end_date)

    totals = (
        await db.execute(
            select(
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
                func.count(Expense.expense_id).label("count"),
            ).where(*filters)
        )
    ).one()

    total_spent = Decimal(totals.total)

    if start_date and end_date:
        num_days = (end_date - start_date).days + 1
    elif start_date:
        num_days = (date.today() - start_date).days + 1
    else:
        num_days = 30
    avg_per_day = round(total_spent / num_days, 2) if num_days > 0 else Decimal(0)

    top_cat = (
        await db.execute(
            select(
                Category.category_id,
                Category.name,
                Category.color,
                Category.icon,
                func.sum(Expense.amount).label("cat_total"),
            )
            .join(Category, Expense.category_id == Category.category_id)
            .where(*filters)
            .group_by(
                Category.category_id,
                Category.name,
                Category.color,
                Category.icon,
            )
            .order_by(func.sum(Expense.amount).desc())
            .limit(1)
        )
    ).one_or_none()

    return {
        "start_date": start_date,
        "end_date": end_date,
        "total_spent": total_spent,
        "transaction_count": totals.count,
        "avg_per_day": avg_per_day,
        "top_category": (
            {
                "category_id": top_cat.category_id,
                "name": top_cat.name,
                "color": top_cat.color,
                "icon": top_cat.icon,
                "total": Decimal(top_cat.cat_total),
            }
            if top_cat
            else None
        ),
    }


# ── GET /by-category ──────────────────────────────────────────────────────────


@router.get("/by-category")
async def get_by_category(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = _expense_filters(current_user.user_id, start_date, end_date)

    rows = (
        await db.execute(
            select(
                Category.category_id,
                Category.name,
                Category.color,
                Category.icon,
                func.sum(Expense.amount).label("total"),
                func.count(Expense.expense_id).label("count"),
            )
            .join(Category, Expense.category_id == Category.category_id)
            .where(*filters)
            .group_by(
                Category.category_id,
                Category.name,
                Category.color,
                Category.icon,
            )
            .order_by(func.sum(Expense.amount).desc())
        )
    ).all()

    grand_total = sum(Decimal(r.total) for r in rows)

    return {
        "start_date": start_date,
        "end_date": end_date,
        "grand_total": grand_total,
        "breakdown": [
            {
                "category_id": r.category_id,
                "name": r.name,
                "color": r.color,
                "icon": r.icon,
                "total": Decimal(r.total),
                "transaction_count": r.count,
                "percentage": (
                    round(float(Decimal(r.total) / grand_total * 100), 1)
                    if grand_total
                    else 0.0
                ),
            }
            for r in rows
        ],
    }


# ── GET /monthly-trend ────────────────────────────────────────────────────────


@router.get("/monthly-trend")
async def get_monthly_trend(
    months: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()

    # calculate start of window
    start_of_window = today.replace(day=1)
    for _ in range(months - 1):
        start_of_window = (start_of_window - timedelta(days=1)).replace(day=1)

    # FIX: reuse same expression
    month_expr = func.date_trunc("month", Expense.expense_date)

    rows = (
        await db.execute(
            select(
                month_expr.label("month"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.expense_id).label("count"),
            )
            .where(
                Expense.user_id == current_user.user_id,
                Expense.expense_date >= start_of_window,
            )
            .group_by(month_expr)
            .order_by(month_expr)
        )
    ).all()

    # map results
    month_map = {r.month.date().replace(day=1): r for r in rows}

    trend = []
    cursor = start_of_window
    while cursor <= today.replace(day=1):
        row = month_map.get(cursor)
        trend.append(
            {
                "year": cursor.year,
                "month": cursor.month,
                "month_label": cursor.strftime("%b %Y"),
                "total": Decimal(row.total) if row else Decimal(0),
                "transaction_count": row.count if row else 0,
            }
        )

        next_month = cursor.replace(day=28) + timedelta(days=4)
        cursor = next_month.replace(day=1)

    return {"months": months, "trend": trend}


# ── GET /export ───────────────────────────────────────────────────────────────


@router.get("/export")
async def export_csv(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = _expense_filters(current_user.user_id, start_date, end_date)
    if category_id:
        filters.append(Expense.category_id == category_id)

    rows = (
        await db.execute(
            select(
                Expense.expense_id,
                Expense.title,
                Expense.amount,
                Expense.currency,
                Expense.expense_date,
                Expense.payment_method,
                Expense.description,
                Expense.tags,
                Category.name.label("category_name"),
            )
            .outerjoin(Category, Expense.category_id == Category.category_id)
            .where(*filters)
            .order_by(Expense.expense_date.desc())
        )
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "ID",
            "Title",
            "Amount",
            "Currency",
            "Date",
            "Category",
            "Payment Method",
            "Description",
            "Tags",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.expense_id,
                r.title,
                r.amount,
                r.currency,
                r.expense_date,
                r.category_name or "",
                r.payment_method.value if r.payment_method else "",
                r.description or "",
                ", ".join(r.tags) if r.tags else "",
            ]
        )

    buffer.seek(0)
    start_str = str(start_date) if start_date else "all"
    end_str = str(end_date) if end_date else "all"
    filename = f"expenses_{start_str}_{end_str}.csv"

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
