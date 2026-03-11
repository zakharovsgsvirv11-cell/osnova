from pydantic import BaseModel


class MonthlySummaryItem(BaseModel):
    month: str  # 'YYYY-MM'
    income: float
    expense: float
    balance: float


class CategoryBreakdownItem(BaseModel):
    category_id: int
    category_name: str
    color: str | None
    total: float
    percentage: float


class TrendItem(BaseModel):
    month: str
    income: float
    expense: float


class BalanceResponse(BaseModel):
    total_income: float
    total_expense: float
    balance: float
