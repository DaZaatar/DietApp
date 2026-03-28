from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.modules.tracking.schemas import (
    AttachmentResponse,
    TrackingMealItemResponse,
    TrackingEntryResponse,
    TrackingEntryUpdate,
)
from app.modules.tracking.service import TrackingService

router = APIRouter()
service = TrackingService()


@router.get("/meals", response_model=list[TrackingMealItemResponse])
def list_tracking_meals(
    meal_plan_id: int | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return service.list_meals(db, user_id=user_id, meal_plan_id=meal_plan_id)


@router.patch("/meals/{meal_id}", response_model=TrackingEntryResponse)
def update_tracking_entry(
    meal_id: int,
    payload: TrackingEntryUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    entry = service.update_status(db, user_id=user_id, meal_id=meal_id, payload=payload)
    return entry


@router.post("/meals/{meal_id}/attachments", response_model=AttachmentResponse)
async def attach_meal_image(
    meal_id: int,
    file: UploadFile = File(...),
    note: str | None = Form(default=None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    attachment = await service.attach_image(db, user_id=user_id, meal_id=meal_id, file=file, note=note)
    return attachment
