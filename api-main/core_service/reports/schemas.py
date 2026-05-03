from pydantic import BaseModel, Field, model_validator
from datetime import datetime

class ReportRequestSchema(BaseModel):
    start_date : datetime = Field()
    end_date : datetime = Field()

    @model_validator(mode='after')
    def check_correct_period(self):
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        return self