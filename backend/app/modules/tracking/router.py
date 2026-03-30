from datetime import date

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.modules.tracking.schemas import (
    AttachmentResponse,
    SwapDaysRequest,
    SwapMealsRequest,
    TrackingReportGroupBy,
    TrackingReportMode,
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


@router.get("/reports/html", response_class=HTMLResponse)
def tracking_report_html(
    start_date: date | None = None,
    end_date: date | None = None,
    group_by: TrackingReportGroupBy = Query(default=TrackingReportGroupBy.daily),
    mode: TrackingReportMode = Query(default=TrackingReportMode.timeline),
    meal_plan_id: int | None = None,
    auto_print: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return service.build_html_report(
        db,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        group_by=group_by.value,
        mode=mode.value,
        meal_plan_id=meal_plan_id,
        auto_print=auto_print,
    )


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


@router.post("/swap/meals")
def swap_meals(
    payload: SwapMealsRequest,
    _user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service.swap_meal_plans_between_meals(db, payload.meal_id_a, payload.meal_id_b)
    return {"ok": True}


@router.post("/swap/days")
def swap_days(
    payload: SwapDaysRequest,
    _user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service.swap_days_in_plan(db, payload.day_id_a, payload.day_id_b)
    return {"ok": True}
