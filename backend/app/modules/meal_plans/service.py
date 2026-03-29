from collections.abc import Sequence
from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.imports.ingredient_categories import normalize_category
from app.modules.models import (
    Day,
    Meal,
    MealAttachment,
    MealIngredient,
    MealPlan,
    MealStatus,
    MealTrackingEntry,
    Week,
)
from app.modules.tracking.storage import LocalMediaStorage


def _resolve_starts_on(raw: object) -> date:
    if raw is None:
        return datetime.now(UTC).date()
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str) and raw.strip():
        return date.fromisoformat(raw.strip()[:10])
    return datetime.now(UTC).date()


def persist_imported_meal_plan(db: Session, payload: dict) -> MealPlan:
    starts_on = _resolve_starts_on(payload.get("starts_on"))
    meal_plan = MealPlan(
        name=payload.get("name", f"Imported {datetime.now(UTC).date()}"),
        starts_on=starts_on,
    )
    db.add(meal_plan)
    db.flush()

    day_index = 0
    for week_data in payload.get("weeks", []):
        week = Week(meal_plan_id=meal_plan.id, week_index=week_data["week_index"])
        db.add(week)
        db.flush()

        for day_data in week_data.get("days", []):
            day = Day(week_id=week.id, day_name=day_data["day"], day_index=day_index)
            day_index += 1
            db.add(day)
            db.flush()

            for meal_data in day_data.get("meals", []):
                meal = Meal(
                    day_id=day.id,
                    meal_type=meal_data["meal_type"],
                    title=meal_data["title"],
                )
                db.add(meal)
                db.flush()

                ingredients = meal_data.get("ingredients", [])
                if not ingredients:
                    ingredients = [{"name": meal_data["title"], "quantity": "1", "unit": "pcs", "category": "other"}]

                for ingredient in ingredients:
                    db.add(
                        MealIngredient(
                            meal_id=meal.id,
                            name=ingredient.get("name", "ingredient"),
                            quantity=str(ingredient.get("quantity", "1")),
                            unit=ingredient.get("unit", "pcs"),
                            category=normalize_category(ingredient.get("category")),
                        )
                    )

    db.commit()
    db.refresh(meal_plan)
    return meal_plan


def list_meals_for_plan(db: Session, meal_plan_id: int) -> Sequence[Meal]:
    stmt = (
        select(Meal)
        .join(Day, Meal.day_id == Day.id)
        .join(Week, Day.week_id == Week.id)
        .where(Week.meal_plan_id == meal_plan_id)
    )
    return db.scalars(stmt).all()


def delete_meal_plan(db: Session, meal_plan_id: int) -> None:
    plan = db.get(MealPlan, meal_plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Meal plan not found")

    meal_ids = list(
        db.scalars(
            select(Meal.id)
            .join(Day, Meal.day_id == Day.id)
            .join(Week, Day.week_id == Week.id)
            .where(Week.meal_plan_id == meal_plan_id)
        ).all()
    )

    if meal_ids:
        tracking_ids = list(
            db.scalars(select(MealTrackingEntry.id).where(MealTrackingEntry.meal_id.in_(meal_ids))).all()
        )
        if tracking_ids:
            storage_keys = list(
                db.scalars(
                    select(MealAttachment.storage_key).where(MealAttachment.tracking_entry_id.in_(tracking_ids))
                ).all()
            )
            media = LocalMediaStorage(settings.media_local_root)
            for key in storage_keys:
                media.delete_file(key)
            db.execute(delete(MealAttachment).where(MealAttachment.tracking_entry_id.in_(tracking_ids)))
        db.execute(delete(MealTrackingEntry).where(MealTrackingEntry.meal_id.in_(meal_ids)))

    db.delete(plan)
    db.commit()


def get_or_create_tracking_entry(db: Session, user_id: int, meal_id: int) -> MealTrackingEntry:
    entry = db.scalar(
        select(MealTrackingEntry).where(
            MealTrackingEntry.user_id == user_id,
            MealTrackingEntry.meal_id == meal_id,
        )
    )
    if entry:
        return entry

    meal = db.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    entry = MealTrackingEntry(user_id=user_id, meal_id=meal_id, status=MealStatus.planned)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
