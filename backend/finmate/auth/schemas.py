from pydantic import Field, BaseModel, EmailStr, model_validator



class RegisterSchema(BaseModel):
    username : str = Field(min_length=4, max_length=32)
    password : str = Field(min_length=6, max_length=32)
    confirm_password : str = Field()
    email : EmailStr

    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match.")
        return self


class LoginSchema(BaseModel):
    email : EmailStr
    password: str = Field(min_length=1)