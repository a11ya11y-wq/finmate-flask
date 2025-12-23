from pydantic import BaseModel, Field




class CategoryCreateSchema(BaseModel):
    name : str = Field(min_length=1, max_length=128)
    mcc_code : str | None = Field(None, max_length=200)
    icon : str = Field(default='bi-tag-fill', max_length=50)
    #TODO: Логіку для валідації мсс кодов добавить


class CategoryUpdateSchema(BaseModel):
    name : str | None = Field(None, min_length=1, max_length=128)
    mcc_code: str | None = Field(None, max_length=200)
    icon: str | None = Field(None, max_length=50)