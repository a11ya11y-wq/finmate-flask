from pydantic import BaseModel, Field, model_validator
from typing import Literal


class ProfileUpdateSchema(BaseModel):
    username : str | None = Field(None, min_length=4, max_length=32)
    currency: Literal['USD', 'EUR', 'UAH'] | None = None
    avatar : str | None = Field(None, min_length=5, max_length=200)


class PasswordChangeSchema(BaseModel):
    old_password: str = Field(min_length=1)
    new_password : str = Field(min_length=6, max_length=32)
    confirm_password : str = Field(min_length=1)

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError('New password and confirmation do not match')
        if self.new_password == self.old_password:
            raise ValueError('New password cannot be the same as old password')
        return self


class MonoTokenUpdateSchema(BaseModel):
    token : str = Field(min_length=44, max_length=44)