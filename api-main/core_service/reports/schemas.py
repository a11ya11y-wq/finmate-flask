from pydantic import BaseModel, Field, model_validator
from datetime import datetime

class ReportRequestSchema(BaseModel):
    startDate : datetime = Field()
    endDate : datetime = Field()

    @model_validator(mode='after')
    def check_correct_period(self):
        if self.startDate >= self.endDate:
            raise ValueError("Start date must be before end date")
        return self