from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.modules.models import Day, Meal, MealIngredient, MealPlan, ShoppingChecklistEntry, Week


class ShoppingService:
    CATEGORY_ORDER = {
        "meats": 1,
        "protein": 1,  # legacy imports
        "dairy": 2,
        "bread": 3,
        "grains": 4,
        "fruits": 5,
        "vegetables": 6,
        "fats": 7,
        "spices": 8,
        "nuts": 9,
        "other": 99,
    }

    @staticmethod
    def _group_key(category: str, name: str, unit: str) -> str:
        return f"{category.strip().lower()}|{name.strip().lower()}|{unit.strip().lower()}"

    @staticmethod
    def _format_decimal(value: Decimal) -> str:
        normalized = value.normalize()
        as_text = format(normalized, "f")
        if "." in as_text:
            as_text = as_text.rstrip("0").rstrip(".")
        return as_text or "0"

    def list_for_user(self, db: Session, user_id: int, meal_plan_id: int | None = None):
        selected_plan = None
        if meal_plan_id is None:
            selected_plan = db.scalar(select(MealPlan).order_by(MealPlan.id.desc()))
        else:
            selected_plan = db.get(MealPlan, meal_plan_id)

        if selected_plan is None:
            raise HTTPException(status_code=404, detail="Meal plan not found")

        rows = db.execute(
            select(
                MealIngredient.id.label("ingredient_id"),
                MealIngredient.name.label("ingredient_name"),
                MealIngredient.quantity.label("quantity"),
                MealIngredient.unit.label("unit"),
                MealIngredient.category.label("category"),
                ShoppingChecklistEntry.checked.label("checked"),
            )
            .join(Meal, MealIngredient.meal_id == Meal.id)
            .join(Day, Meal.day_id == Day.id)
            .join(Week, Day.week_id == Week.id)
            .outerjoin(
                ShoppingChecklistEntry,
                and_(
                    ShoppingChecklistEntry.meal_ingredient_id == MealIngredient.id,
                    ShoppingChecklistEntry.user_id == user_id,
                ),
            )
            .where(Week.meal_plan_id == selected_plan.id)
            .order_by(Week.week_index.asc(), Day.id.asc(), Meal.id.asc(), MealIngredient.id.asc())
        ).all()

        grouped: dict[str, dict] = {}
        for row in rows:
            category = (row.category or "other").strip().lower()
            key = self._group_key(category, row.ingredient_name, row.unit)
            if key not in grouped:
                grouped[key] = {
                    "id": key,
                    "category": category,
                    "name": row.ingredient_name.strip(),
                    "unit": row.unit.strip(),
                    "quantity_total": Decimal("0"),
                    "all_checked": True,
                    "has_any": False,
                }
            try:
                grouped[key]["quantity_total"] += Decimal(str(row.quantity).strip())
            except (InvalidOperation, ValueError):
                continue
            grouped[key]["has_any"] = True
            grouped[key]["all_checked"] = grouped[key]["all_checked"] and bool(row.checked)

        items = [
            {
                "id": key,
                "category": value["category"],
                "name": value["name"],
                "quantity": self._format_decimal(value["quantity_total"]),
                "unit": value["unit"],
                "checked": value["all_checked"],
            }
            for key, value in sorted(
                grouped.items(),
                key=lambda kv: (
                    self.CATEGORY_ORDER.get(kv[1]["category"], 99),
                    kv[1]["name"].lower(),
                    kv[1]["unit"].lower(),
                ),
            )
            if value["has_any"]
        ]

        return {
            "meal_plan_id": selected_plan.id,
            "meal_plan_name": selected_plan.name,
            "generated_at": datetime.now(UTC),
            "items": items,
        }

    def set_group_checked(self, db: Session, user_id: int, meal_plan_id: int, item_key: str, checked: bool):
        try:
            raw_category, raw_name, raw_unit = item_key.split("|", 2)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid shopping item key") from exc

        ingredients = db.execute(
            select(MealIngredient.id)
            .join(Meal, MealIngredient.meal_id == Meal.id)
            .join(Day, Meal.day_id == Day.id)
            .join(Week, Day.week_id == Week.id)
            .where(
                Week.meal_plan_id == meal_plan_id,
                MealIngredient.category.ilike(raw_category),
                MealIngredient.name.ilike(raw_name),
                MealIngredient.unit.ilike(raw_unit),
            )
        ).all()
        if not ingredients:
            raise HTTPException(status_code=404, detail="Shopping item not found")

        now = datetime.now(UTC).replace(tzinfo=None)
        for ingredient_row in ingredients:
            ingredient_id = ingredient_row.id
            entry = db.scalar(
                select(ShoppingChecklistEntry).where(
                    ShoppingChecklistEntry.user_id == user_id,
                    ShoppingChecklistEntry.meal_ingredient_id == ingredient_id,
                )
            )
            if entry is None:
                entry = ShoppingChecklistEntry(
                    user_id=user_id,
                    meal_ingredient_id=ingredient_id,
                    checked=checked,
                    updated_at=now,
                )
                db.add(entry)
            else:
                entry.checked = checked
                entry.updated_at = now

        db.commit()
        return {"ok": True}
