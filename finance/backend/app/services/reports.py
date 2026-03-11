from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction


async def get_monthly_summary(db: AsyncSession, user_id: int, year: int) -> list[dict]:
    """Доходы vs расходы по месяцам за указанный год."""
    stmt = (
        select(
            func.substr(Transaction.date, 1, 7).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .where(Transaction.user_id == user_id)
        .where(Transaction.date.like(f"{year}-%"))
        .group_by("month", Transaction.type)
        .order_by("month")
    )
    result = await db.execute(stmt)
    rows = result.all()

    months: dict[str, dict] = {}
    for month, tx_type, total in rows:
        if month not in months:
            months[month] = {"month": month, "income": 0.0, "expense": 0.0}
        months[month][tx_type] = total

    for item in months.values():
        item["balance"] = item["income"] - item["expense"]

    return list(months.values())


async def get_category_breakdown(
    db: AsyncSession, user_id: int, date_from: str, date_to: str, tx_type: str
) -> list[dict]:
    """Итого по категориям за период."""
    stmt = (
        select(
            Category.id,
            Category.name,
            Category.color,
            func.sum(Transaction.amount).label("total"),
        )
        .join(Transaction, Transaction.category_id == Category.id)
        .where(Transaction.user_id == user_id)
        .where(Transaction.type == tx_type)
        .where(Transaction.date >= date_from)
        .where(Transaction.date <= date_to)
        .group_by(Category.id, Category.name, Category.color)
        .order_by(func.sum(Transaction.amount).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    grand_total = sum(r.total for r in rows) or 1.0
    return [
        {
            "category_id": r.id,
            "category_name": r.name,
            "color": r.color,
            "total": r.total,
            "percentage": round(r.total / grand_total * 100, 1),
        }
        for r in rows
    ]


async def get_trend(db: AsyncSession, user_id: int, months: int = 12) -> list[dict]:
    """Тренд доходов/расходов за последние N месяцев."""
    stmt = (
        select(
            func.substr(Transaction.date, 1, 7).label("month"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
        )
        .where(Transaction.user_id == user_id)
        .group_by("month", Transaction.type)
        .order_by(func.substr(Transaction.date, 1, 7).desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    data: dict[str, dict] = {}
    for month, tx_type, total in rows:
        if month not in data:
            data[month] = {"month": month, "income": 0.0, "expense": 0.0}
        data[month][tx_type] = total

    sorted_months = sorted(data.values(), key=lambda x: x["month"], reverse=True)[:months]
    return list(reversed(sorted_months))


async def get_balance(db: AsyncSession, user_id: int) -> dict:
    """Общий баланс: доходы - расходы."""
    stmt = (
        select(Transaction.type, func.sum(Transaction.amount).label("total"))
        .where(Transaction.user_id == user_id)
        .group_by(Transaction.type)
    )
    result = await db.execute(stmt)
    totals = {r.type: r.total for r in result.all()}

    income = totals.get("income", 0.0)
    expense = totals.get("expense", 0.0)
    return {"total_income": income, "total_expense": expense, "balance": income - expense}
