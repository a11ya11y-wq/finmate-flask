from pydantic import Field, BaseModel, EmailStr



class RegisterSchema(BaseModel):
    username : str = Field(min_length=4, max_length=32)
    password : str = Field(min_length=6, max_length=32)
    confirm_password : str = Field()
    email : EmailStr


class LoginSchema(BaseModel):
    email : EmailStr
    password: str = Field(min_length=1)