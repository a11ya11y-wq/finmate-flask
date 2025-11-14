from pydantic import BaseModel, Field
from typing import Literal


class ProfileUpdateSchema(BaseModel):
    username : str | None = Field(None, min_length=4, max_length=32)


class PasswordChangeSchema(BaseModel):
    old_password: str = Field(min_length=1)
    new_password : str = Field(min_length=6, max_length=32)
    confirm_password : str = Field(min_length=1)


class CurrencyUpdateSchema(BaseModel):
    currency : Literal['USD', 'EUR', 'UAH']


class MonoTokenUpdateSchema(BaseModel):
    token : str = Field(min_length=10)