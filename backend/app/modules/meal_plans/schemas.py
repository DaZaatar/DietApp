from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MealPlanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    starts_on: date | None = None
    created_at: datetime
