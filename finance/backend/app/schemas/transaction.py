from enum import Enum

from pydantic import BaseModel, field_validator


class TransactionType(str, Enum):
    INCOME = "доход"
    EXPENSE = "расход"


class TransactionCreate(BaseModel):
    category_id: int
    amount: float
    type: TransactionType
    description: str | None = None
    date: str  # 'YYYY-MM-DD'

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return v

    @field_validator("date")
    @classmethod
    def date_format(cls, v):
        import re
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Дата должна быть в формате YYYY-MM-DD")
        return v


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    amount: float | None = None
    type: TransactionType | None = None
    description: str | None = None
    date: str | None = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Сумма должна быть больше нуля")
        return v


class TransactionResponse(BaseModel):
    id: int
    category_id: int
    amount: float
    type: str
    description: str | None
    date: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    per_page: int
