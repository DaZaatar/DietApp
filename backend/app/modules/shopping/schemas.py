from datetime import datetime

from pydantic import BaseModel


class ShoppingListItemResponse(BaseModel):
    id: str
    category: str
    name: str
    quantity: str
    unit: str
    checked: bool


class ShoppingChecklistUpdate(BaseModel):
    meal_plan_id: int
    checked: bool


class ShoppingListResponse(BaseModel):
    meal_plan_id: int
    meal_plan_name: str
    generated_at: datetime
    items: list[ShoppingListItemResponse]
