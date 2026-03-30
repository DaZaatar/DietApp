from datetime import UTC, date, datetime, timedelta
from html import escape

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

    def _resolve_report_date_range(self, start_date: date | None, end_date: date | None) -> tuple[date, date]:
        today = datetime.now(UTC).date()
        if start_date is None and end_date is None:
            return (today - timedelta(days=13), today)
        if start_date is None:
            return (end_date, end_date)  # type: ignore[arg-type]
        if end_date is None:
            return (start_date, start_date)
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
        return (start_date, end_date)

    def _build_report_bucket(
        self,
        meal_date: date,
        group_by: str,
        start_date: date,
    ) -> tuple[str, date, date, str]:
        if group_by == "daily":
            label = meal_date.strftime("%a, %b %d, %Y")
            return (f"d-{meal_date.isoformat()}", meal_date, meal_date, label)

        if group_by == "weekly":
            bucket_start = meal_date - timedelta(days=meal_date.weekday())
            bucket_end = bucket_start + timedelta(days=6)
            iso_week = meal_date.isocalendar().week
            label = f"Week {iso_week}: {bucket_start.isoformat()} to {bucket_end.isoformat()}"
            return (f"w-{bucket_start.isoformat()}", bucket_start, bucket_end, label)

        # biweekly buckets are anchored to the selected start date.
        span_index = (meal_date - start_date).days // 14
        bucket_start = start_date + timedelta(days=span_index * 14)
        bucket_end = bucket_start + timedelta(days=13)
        label = f"Bi-week: {bucket_start.isoformat()} to {bucket_end.isoformat()}"
        return (f"bw-{bucket_start.isoformat()}", bucket_start, bucket_end, label)

    def build_html_report(
        self,
        db: Session,
        user_id: int,
        start_date: date | None = None,
        end_date: date | None = None,
        group_by: str = "daily",
        meal_plan_id: int | None = None,
        auto_print: bool = False,
    ) -> str:
        start, end = self._resolve_report_date_range(start_date, end_date)
        if group_by not in {"daily", "weekly", "biweekly"}:
            raise HTTPException(status_code=400, detail="Unsupported grouping mode")

        stmt = (
            select(
                Meal.id.label("meal_id"),
                Meal.title.label("title"),
                Meal.meal_type.label("meal_type"),
                Day.day_name.label("day_name"),
                Day.day_index.label("day_index"),
                Week.week_index.label("week_index"),
                MealPlan.id.label("meal_plan_id"),
                MealPlan.name.label("meal_plan_name"),
                MealPlan.starts_on.label("plan_starts_on"),
                MealPlan.created_at.label("plan_created_at"),
                MealTrackingEntry.status.label("status"),
                MealTrackingEntry.notes.label("notes"),
                MealTrackingEntry.eaten_at.label("eaten_at"),
            )
            .join(Day, Meal.day_id == Day.id)
            .join(Week, Day.week_id == Week.id)
            .join(MealPlan, Week.meal_plan_id == MealPlan.id)
            .outerjoin(
                MealTrackingEntry,
                and_(MealTrackingEntry.meal_id == Meal.id, MealTrackingEntry.user_id == user_id),
            )
            .order_by(MealPlan.id.asc(), Day.day_index.asc(), Meal.id.asc())
        )
        if meal_plan_id is not None:
            stmt = stmt.where(Week.meal_plan_id == meal_plan_id)

        rows = db.execute(stmt).all()
        grouped: dict[str, dict] = {}
        totals = {
            MealStatus.planned.value: 0,
            MealStatus.eaten.value: 0,
            MealStatus.skipped.value: 0,
        }
        total_meals = 0

        for row in rows:
            base_date = row.plan_starts_on or row.plan_created_at.date()
            meal_date = base_date + timedelta(days=row.day_index or 0)
            if meal_date < start or meal_date > end:
                continue

            status = row.status.value if isinstance(row.status, MealStatus) else MealStatus.planned.value
            bucket_key, bucket_start, _bucket_end, bucket_label = self._build_report_bucket(meal_date, group_by, start)
            if bucket_key not in grouped:
                grouped[bucket_key] = {
                    "start": bucket_start,
                    "label": bucket_label,
                    "totals": {
                        MealStatus.planned.value: 0,
                        MealStatus.eaten.value: 0,
                        MealStatus.skipped.value: 0,
                    },
                    "rows": [],
                }

            grouped[bucket_key]["totals"][status] += 1
            grouped[bucket_key]["rows"].append(
                {
                    "meal_date": meal_date.isoformat(),
                    "meal_plan_id": row.meal_plan_id,
                    "meal_plan_name": row.meal_plan_name,
                    "day_name": row.day_name,
                    "week_index": row.week_index,
                    "meal_type": row.meal_type,
                    "title": row.title,
                    "status": status,
                    "notes": row.notes,
                    "eaten_at": row.eaten_at.isoformat(sep=" ", timespec="minutes") if row.eaten_at else "",
                }
            )
            totals[status] += 1
            total_meals += 1

        ordered_groups = sorted(grouped.values(), key=lambda g: g["start"])
        generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
        escaped_range = f"{start.isoformat()} to {end.isoformat()}"
        escaped_group_by = group_by.capitalize()
        plan_scope = f"Meal plan filter: #{meal_plan_id}" if meal_plan_id is not None else "Meal plan filter: all plans"

        groups_html_parts: list[str] = []
        if not ordered_groups:
            groups_html_parts.append("<p>No meals found in this date range.</p>")
        else:
            for group in ordered_groups:
                row_html = []
                for item in group["rows"]:
                    notes = escape(item["notes"]) if item["notes"] else "-"
                    eaten_at = escape(item["eaten_at"]) if item["eaten_at"] else "-"
                    row_html.append(
                        "<tr>"
                        f"<td>{escape(item['meal_date'])}</td>"
                        f"<td>{escape(item['meal_plan_name'])} (#{item['meal_plan_id']})</td>"
                        f"<td>W{item['week_index']} · {escape(item['day_name'])}</td>"
                        f"<td>{escape(item['meal_type'])}</td>"
                        f"<td>{escape(item['title'])}</td>"
                        f"<td class='status-{escape(item['status'])}'>{escape(item['status'])}</td>"
                        f"<td>{notes}</td>"
                        f"<td>{eaten_at}</td>"
                        "</tr>"
                    )
                groups_html_parts.append(
                    f"""
                    <section class="group">
                      <h3>{escape(group['label'])}</h3>
                      <p class="group-summary">
                        Planned: <strong>{group['totals'][MealStatus.planned.value]}</strong> ·
                        Eaten: <strong>{group['totals'][MealStatus.eaten.value]}</strong> ·
                        Skipped: <strong>{group['totals'][MealStatus.skipped.value]}</strong>
                      </p>
                      <div class="table-wrap">
                        <table>
                          <thead>
                            <tr>
                              <th>Date</th>
                              <th>Meal plan</th>
                              <th>Day</th>
                              <th>Meal type</th>
                              <th>Meal title</th>
                              <th>Status</th>
                              <th>Notes</th>
                              <th>Eaten at</th>
                            </tr>
                          </thead>
                          <tbody>
                            {"".join(row_html)}
                          </tbody>
                        </table>
                      </div>
                    </section>
                    """
                )

        auto_print_script = (
            "<script>window.addEventListener('load', () => window.print());</script>" if auto_print else ""
        )

        return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Meal Tracking Report</title>
    <style>
      :root {{
        color-scheme: light;
        font-family: Arial, Helvetica, sans-serif;
      }}
      body {{
        margin: 1.25rem;
        color: #0f172a;
      }}
      h1, h2, h3 {{
        margin: 0 0 0.6rem;
      }}
      .meta {{
        margin-bottom: 1rem;
        font-size: 0.95rem;
        color: #334155;
      }}
      .totals {{
        border: 1px solid #cbd5e1;
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 0.75rem 0 1.25rem;
        background: #f8fafc;
      }}
      .group {{
        margin: 1rem 0 1.5rem;
      }}
      .group-summary {{
        margin: 0.35rem 0 0.6rem;
      }}
      .table-wrap {{
        overflow-x: auto;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
      }}
      th, td {{
        border: 1px solid #cbd5e1;
        padding: 0.45rem;
        text-align: left;
        vertical-align: top;
        font-size: 0.9rem;
      }}
      th {{
        background: #f1f5f9;
      }}
      .status-planned {{
        color: #334155;
        font-weight: 600;
      }}
      .status-eaten {{
        color: #166534;
        font-weight: 700;
      }}
      .status-skipped {{
        color: #92400e;
        font-weight: 700;
      }}
      @media print {{
        body {{
          margin: 0.5in;
        }}
        .no-print {{
          display: none;
        }}
      }}
    </style>
    {auto_print_script}
  </head>
  <body>
    <h1>Meal Tracking Report</h1>
    <p class="meta">Generated: {escape(generated_at)}</p>
    <p class="meta">Date range: {escape(escaped_range)} · Grouping: {escape(escaped_group_by)} · {escape(plan_scope)}</p>
    <section class="totals">
      <h2>Summary totals</h2>
      <p>Total meals: <strong>{total_meals}</strong></p>
      <p>
        Planned: <strong>{totals[MealStatus.planned.value]}</strong> ·
        Eaten: <strong>{totals[MealStatus.eaten.value]}</strong> ·
        Skipped: <strong>{totals[MealStatus.skipped.value]}</strong>
      </p>
      <p class="no-print">Tip: use your browser Print dialog to Save as PDF.</p>
    </section>
    <section>
      <h2>Breakdown</h2>
      {"".join(groups_html_parts)}
    </section>
  </body>
</html>
"""

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
