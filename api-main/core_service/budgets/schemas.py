from pydantic import BaseModel, Field
from decimal import Decimal


class BudgetSchema(BaseModel):
    amount : Decimal = Field(gt=0, decimal_places=2, max_digits=10)
    category_id : int
    is_recurring : bool

