from datetime import datetime, timezone

from pydantic import BaseModel, Field
from decimal import  Decimal
from typing import Literal, Optional

class TransactionCreateSchema(BaseModel):
    amount : Decimal = Field(gt=0, decimal_places=2)
    title : str = Field(min_length=1, max_length=128)
    transaction_type : Literal['income','expense']
    category_id : int
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    note: str | None = Field(None, max_length=128)


class TransactionUpdateSchema(BaseModel):
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    title: Optional[str] = Field(None, min_length=1, max_length=128)
    transaction_type: Optional[Literal['income', 'expense']] = None
    category_id: Optional[int] = None
    created_at: Optional[datetime] = None
    note: Optional[str] = Field(None, max_length=128)