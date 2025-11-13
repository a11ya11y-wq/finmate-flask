from pydantic import BaseModel, Field




class CategoryCreateSchema(BaseModel):
    name : str = Field(min_length=1, max_length=128)
    mcc_code : str | None = Field(max_length=200)


class CategoryUpdateSchema(BaseModel):
    name : str | None = Field(min_length=1, max_length=128)
    mcc_code: str | None = Field(max_length=200)