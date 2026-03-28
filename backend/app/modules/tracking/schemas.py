from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.models import MealStatus


class TrackingEntryUpdate(BaseModel):
    status: MealStatus
    notes: str | None = None
    eaten_at: datetime | None = None


class TrackingEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    meal_id: int
    user_id: int
    status: MealStatus
    notes: str | None
    eaten_at: datetime | None


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tracking_entry_id: int
    storage_key: str
    original_filename: str
    mime_type: str
    file_size: int
    note: str | None


class TrackingIngredientItem(BaseModel):
    name: str
    quantity: str
    unit: str
    category: str


class TrackingMealItemResponse(BaseModel):
    meal_id: int
    meal_plan_id: int
    week_index: int
    day_name: str
    meal_type: str
    title: str
    status: MealStatus
    notes: str | None
    eaten_at: datetime | None
    ingredients: list[TrackingIngredientItem]
