from pydantic import BaseModel, Field, model_validator
from datetime import date

class ReportRequestSchema(BaseModel):
    startDate : date = Field()
    endDate : date = Field()

    @model_validator(mode='after')
    def check_correct_period(self):
        if self.startDate >= self.endDate:
            raise ValueError("Start date must be before end date")
        return self