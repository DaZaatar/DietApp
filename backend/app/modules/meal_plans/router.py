from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.meal_plans.schemas import MealPlanSummary
from app.modules.meal_plans.service import delete_meal_plan
from app.modules.models import MealPlan

router = APIRouter()


@router.get("", response_model=list[MealPlanSummary])
def list_meal_plans(db: Session = Depends(get_db)):
    rows = db.scalars(select(MealPlan).order_by(MealPlan.id.desc())).all()
    return [MealPlanSummary.model_validate(r) for r in rows]


@router.delete("/{meal_plan_id}")
def remove_meal_plan(meal_plan_id: int, db: Session = Depends(get_db)):
    delete_meal_plan(db, meal_plan_id)
    return {"ok": True}
