from pydantic import BaseModel


class TransactionCreate(BaseModel):
    category_id: int
    amount: float
    type: str  # 'доход' | 'расход'
    description: str | None = None
    date: str  # 'YYYY-MM-DD'


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    amount: float | None = None
    type: str | None = None
    description: str | None = None
    date: str | None = None


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
