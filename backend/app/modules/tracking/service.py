from datetime import UTC, datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy import and_, select, update as sa_update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.meal_plans.service import get_or_create_tracking_entry
from app.modules.models import Day, Meal, MealAttachment, MealIngredient, MealPlan, MealStatus, MealTrackingEntry, Week
from app.modules.tracking.schemas import TrackingEntryUpdate
from app.modules.tracking.storage import LocalMediaStorage


class TrackingService:
    def __init__(self) -> None:
        self.storage = LocalMediaStorage(settings.media_local_root)

    def update_status(self, db: Session, user_id: int, meal_id: int, payload: TrackingEntryUpdate):
        entry = get_or_create_tracking_entry(db, user_id=user_id, meal_id=meal_id)
        entry.status = payload.status
        entry.notes = payload.notes
        entry.eaten_at = payload.eaten_at if payload.status == MealStatus.eaten else None
        if payload.status == MealStatus.eaten and entry.eaten_at is None:
            entry.eaten_at = datetime.now(UTC).replace(tzinfo=None)

        db.commit()
        db.refresh(entry)
        return entry

    def list_meals(self, db: Session, user_id: int, meal_plan_id: int | None = None):
        selected_plan_id = meal_plan_id
        if selected_plan_id is None:
            latest_plan = db.scalar(select(MealPlan).order_by(MealPlan.id.desc()))
            if latest_plan is None:
                return []
            selected_plan_id = latest_plan.id

        stmt = (
            select(
                Meal.id.label("meal_id"),
                Day.id.label("day_id"),
                Week.meal_plan_id.label("meal_plan_id"),
                Week.week_index.label("week_index"),
                Day.day_name.label("day_name"),
                Day.day_index.label("day_index"),
                MealPlan.starts_on.label("plan_starts_on"),
                Meal.meal_type.label("meal_type"),
                Meal.title.label("title"),
                MealTrackingEntry.status.label("status"),
                MealTrackingEntry.notes.label("notes"),
                MealTrackingEntry.eaten_at.label("eaten_at"),
            )
            .join(Day, Meal.day_id == Day.id)
            .join(Week, Day.week_id == Week.id)
            .join(MealPlan, MealPlan.id == Week.meal_plan_id)
            .outerjoin(
                MealTrackingEntry,
                and_(MealTrackingEntry.meal_id == Meal.id, MealTrackingEntry.user_id == user_id),
            )
            .where(Week.meal_plan_id == selected_plan_id)
            .order_by(Week.week_index.asc(), Day.id.asc(), Meal.id.asc())
        )

        rows = db.execute(stmt).all()
        meal_ids = [row.meal_id for row in rows]
        ingredients_by_meal: dict[int, list[dict[str, str]]] = {}
        if meal_ids:
            ing_rows = db.execute(
                select(MealIngredient)
                .where(MealIngredient.meal_id.in_(meal_ids))
                .order_by(MealIngredient.meal_id.asc(), MealIngredient.id.asc())
            ).scalars().all()
            for ing in ing_rows:
                ingredients_by_meal.setdefault(ing.meal_id, []).append(
                    {
                        "name": ing.name,
                        "quantity": ing.quantity,
                        "unit": ing.unit,
                        "category": ing.category,
                    }
                )

        return [
            {
                "meal_id": row.meal_id,
                "day_id": row.day_id,
                "meal_plan_id": row.meal_plan_id,
                "week_index": row.week_index,
                "day_name": row.day_name,
                "day_index": row.day_index if row.day_index is not None else 0,
                "plan_starts_on": row.plan_starts_on,
                "meal_type": row.meal_type,
                "title": row.title,
                "status": row.status or MealStatus.planned,
                "notes": row.notes,
                "eaten_at": row.eaten_at,
                "ingredients": ingredients_by_meal.get(row.meal_id, []),
            }
            for row in rows
        ]

    def swap_meal_plans_between_meals(self, db: Session, meal_id_a: int, meal_id_b: int) -> None:
        if meal_id_a == meal_id_b:
            raise HTTPException(status_code=400, detail="Cannot swap a meal with itself")
        meal_a = db.get(Meal, meal_id_a)
        meal_b = db.get(Meal, meal_id_b)
        if not meal_a or not meal_b:
            raise HTTPException(status_code=404, detail="Meal not found")

        day_a = db.get(Day, meal_a.day_id)
        day_b = db.get(Day, meal_b.day_id)
        if not day_a or not day_b:
            raise HTTPException(status_code=404, detail="Day not found")
        week_a = db.get(Week, day_a.week_id)
        week_b = db.get(Week, day_b.week_id)
        if not week_a or not week_b:
            raise HTTPException(status_code=404, detail="Week not found")
        if week_a.meal_plan_id != week_b.meal_plan_id:
            raise HTTPException(status_code=400, detail="Meals must belong to the same meal plan")

        temp = Meal(day_id=meal_a.day_id, meal_type="__swap__", title="__swap__")
        db.add(temp)
        db.flush()

        db.execute(
            sa_update(MealIngredient)
            .where(MealIngredient.meal_id == meal_a.id)
            .values(meal_id=temp.id)
        )
        db.execute(
            sa_update(MealIngredient)
            .where(MealIngredient.meal_id == meal_b.id)
            .values(meal_id=meal_a.id)
        )
        db.execute(
            sa_update(MealIngredient)
            .where(MealIngredient.meal_id == temp.id)
            .values(meal_id=meal_b.id)
        )

        t_type, t_title = meal_a.meal_type, meal_a.title
        meal_a.meal_type, meal_a.title = meal_b.meal_type, meal_b.title
        meal_b.meal_type, meal_b.title = t_type, t_title

        db.delete(temp)
        db.commit()

    def swap_days_in_plan(self, db: Session, day_id_a: int, day_id_b: int) -> None:
        if day_id_a == day_id_b:
            raise HTTPException(status_code=400, detail="Cannot swap a day with itself")
        day_a = db.get(Day, day_id_a)
        day_b = db.get(Day, day_id_b)
        if not day_a or not day_b:
            raise HTTPException(status_code=404, detail="Day not found")
        week_a = db.get(Week, day_a.week_id)
        week_b = db.get(Week, day_b.week_id)
        if not week_a or not week_b:
            raise HTTPException(status_code=404, detail="Week not found")
        if week_a.meal_plan_id != week_b.meal_plan_id:
            raise HTTPException(status_code=400, detail="Days must belong to the same meal plan")

        meals_a = db.scalars(select(Meal).where(Meal.day_id == day_id_a).order_by(Meal.id)).all()
        meals_b = db.scalars(select(Meal).where(Meal.day_id == day_id_b).order_by(Meal.id)).all()
        if len(meals_a) != len(meals_b):
            raise HTTPException(
                status_code=400,
                detail="Both days must have the same number of meals to swap whole days",
            )
        for ma, mb in zip(meals_a, meals_b):
            self.swap_meal_plans_between_meals(db, ma.id, mb.id)

    async def attach_image(
        self,
        db: Session,
        user_id: int,
        meal_id: int,
        file: UploadFile,
        note: str | None = None,
    ):
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed")

        entry = get_or_create_tracking_entry(db, user_id=user_id, meal_id=meal_id)
        storage_key, file_size = await self.storage.save_upload(file, prefix="meal-images")

        attachment = MealAttachment(
            tracking_entry_id=entry.id,
            storage_key=storage_key,
            original_filename=file.filename or "image",
            mime_type=file.content_type,
            file_size=file_size,
            note=note,
        )
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        return attachment
