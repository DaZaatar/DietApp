from datetime import UTC, datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.modules.models import Day, Meal, MealIngredient, MealPlan, MealStatus, MealTrackingEntry, User, Week


def ensure_user(db):
    user = db.scalar(select(User).where(User.email == 'demo@dietapp.local'))
    if user:
        return user
    user = User(email='demo@dietapp.local')
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_sample_plan(db):
    plan = db.scalar(select(MealPlan).where(MealPlan.name == 'Sample Week Plan'))
    if plan:
        return plan

    plan = MealPlan(name='Sample Week Plan')
    db.add(plan)
    db.flush()

    week = Week(meal_plan_id=plan.id, week_index=1)
    db.add(week)
    db.flush()

    days_payload = [
        (
            'Monday',
            [
                ('breakfast', 'Greek yogurt with berries', [('greek yogurt', '250', 'g'), ('berries', '120', 'g')]),
                ('lunch', 'Chicken quinoa bowl', [('chicken breast', '300', 'g'), ('quinoa', '150', 'g')]),
                ('dinner', 'Salmon with vegetables', [('salmon', '400', 'g'), ('vegetables', '500', 'g')]),
            ],
        ),
        (
            'Tuesday',
            [
                ('breakfast', 'Overnight oats', [('oats', '100', 'g'), ('milk', '250', 'ml')]),
                ('lunch', 'Turkey avocado wrap', [('turkey', '250', 'g'), ('avocado', '1', 'pcs')]),
                ('dinner', 'Lentil soup with salad', [('lentils', '300', 'g'), ('salad greens', '200', 'g')]),
            ],
        ),
    ]

    for day_name, meals in days_payload:
        day = Day(week_id=week.id, day_name=day_name)
        db.add(day)
        db.flush()
        for meal_type, title, ingredients in meals:
            meal = Meal(day_id=day.id, meal_type=meal_type, title=title)
            db.add(meal)
            db.flush()
            for name, quantity, unit in ingredients:
                db.add(MealIngredient(meal_id=meal.id, name=name, quantity=quantity, unit=unit))

    db.commit()
    db.refresh(plan)
    return plan


def ensure_tracking_entries(db, user_id: int, meal_plan_id: int):
    meals = db.scalars(
        select(Meal)
        .join(Day, Meal.day_id == Day.id)
        .join(Week, Day.week_id == Week.id)
        .where(Week.meal_plan_id == meal_plan_id)
        .order_by(Meal.id.asc())
    ).all()

    for idx, meal in enumerate(meals):
        entry = db.scalar(
            select(MealTrackingEntry).where(
                MealTrackingEntry.user_id == user_id,
                MealTrackingEntry.meal_id == meal.id,
            )
        )
        if entry:
            continue

        status = MealStatus.planned
        eaten_at = None
        if idx == 0:
            status = MealStatus.eaten
            eaten_at = datetime.now(UTC).replace(tzinfo=None)
        elif idx == 2:
            status = MealStatus.skipped

        db.add(
            MealTrackingEntry(
                user_id=user_id,
                meal_id=meal.id,
                status=status,
                eaten_at=eaten_at,
                notes='Seeded entry' if idx in (0, 2) else None,
            )
        )

    db.commit()


def main():
    db = SessionLocal()
    try:
        user = ensure_user(db)
        plan = ensure_sample_plan(db)
        ensure_tracking_entries(db, user_id=user.id, meal_plan_id=plan.id)
        print(f'Seed complete: user_id={user.id}, meal_plan_id={plan.id}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
