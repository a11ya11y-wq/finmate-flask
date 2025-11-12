from datetime import date

from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Literal, Optional

class TransactionCreateSchema(BaseModel):
    amount : Decimal = Field(gt=0, decimal_places=2)
    title : str = Field(min_length=1, max_length=128)
    transaction_type : Literal['income','expense']
    category_id : int
    created_at : date = Field(default_factory=date.today)
    note: str | None = Field(None, max_length=500)


class TransactionUpdateSchema(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    transaction_type: Optional[Literal['income', 'expense']] = None
    category_id: Optional[int]
    created_at: Optional[date] = Field(default_factory=date.today)
    note: Optional[str] = Field(None, max_length=128)