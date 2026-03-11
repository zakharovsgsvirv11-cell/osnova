from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import BalanceResponse, CategoryBreakdownItem, MonthlySummaryItem, TrendItem
from app.services.reports import get_balance, get_category_breakdown, get_monthly_summary, get_trend

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly-summary", response_model=list[MonthlySummaryItem])
async def monthly_summary(
    year: int = Query(default_factory=lambda: datetime.now().year),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_monthly_summary(db, user.id, year)


@router.get("/category-breakdown", response_model=list[CategoryBreakdownItem])
async def category_breakdown(
    date_from: str = Query(...),
    date_to: str = Query(...),
    type: str = Query(..., pattern="^(income|expense)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_category_breakdown(db, user.id, date_from, date_to, type)


@router.get("/trend", response_model=list[TrendItem])
async def trend(
    months: int = Query(12, ge=1, le=60),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_trend(db, user.id, months)


@router.get("/balance", response_model=BalanceResponse)
async def balance(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_balance(db, user.id)
