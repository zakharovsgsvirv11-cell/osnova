from pydantic import BaseModel

from app.schemas.transaction import TransactionType


class CategoryCreate(BaseModel):
    name: str
    type: TransactionType
    color: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    type: TransactionType | None = None
    color: str | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    type: str
    color: str | None
    is_active: int
    created_at: str

    model_config = {"from_attributes": True}
