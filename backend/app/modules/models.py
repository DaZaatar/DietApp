from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class MealStatus(str, Enum):
    planned = "planned"
    eaten = "eaten"
    skipped = "skipped"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)
    weeks: Mapped[list["Week"]] = relationship(back_populates="meal_plan", cascade="all, delete-orphan")


class Week(Base):
    __tablename__ = "weeks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_plan_id: Mapped[int] = mapped_column(ForeignKey("meal_plans.id"), nullable=False)
    week_index: Mapped[int] = mapped_column(Integer, nullable=False)

    meal_plan: Mapped["MealPlan"] = relationship(back_populates="weeks")
    days: Mapped[list["Day"]] = relationship(back_populates="week", cascade="all, delete-orphan")


class Day(Base):
    __tablename__ = "days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_id: Mapped[int] = mapped_column(ForeignKey("weeks.id"), nullable=False)
    day_name: Mapped[str] = mapped_column(String(30), nullable=False)

    week: Mapped["Week"] = relationship(back_populates="days")
    meals: Mapped[list["Meal"]] = relationship(back_populates="day", cascade="all, delete-orphan")


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_id: Mapped[int] = mapped_column(ForeignKey("days.id"), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    day: Mapped["Day"] = relationship(back_populates="meals")
    ingredients: Mapped[list["MealIngredient"]] = relationship(back_populates="meal", cascade="all, delete-orphan")


class MealTrackingEntry(Base):
    __tablename__ = "meal_tracking_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id"), nullable=False)
    status: Mapped[MealStatus] = mapped_column(SqlEnum(MealStatus), default=MealStatus.planned)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    eaten_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    attachments: Mapped[list["MealAttachment"]] = relationship(
        back_populates="tracking_entry",
        cascade="all, delete-orphan",
    )


class MealAttachment(Base):
    __tablename__ = "meal_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tracking_entry_id: Mapped[int] = mapped_column(ForeignKey("meal_tracking_entries.id"), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    tracking_entry: Mapped["MealTrackingEntry"] = relationship(back_populates="attachments")


class MealIngredient(Base):
    __tablename__ = "meal_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="other")

    meal: Mapped["Meal"] = relationship(back_populates="ingredients")
    checklist_entries: Mapped[list["ShoppingChecklistEntry"]] = relationship(
        back_populates="meal_ingredient",
        cascade="all, delete-orphan",
    )


class ShoppingChecklistEntry(Base):
    __tablename__ = "shopping_checklist_entries"
    __table_args__ = (UniqueConstraint("user_id", "meal_ingredient_id", name="uq_user_meal_ingredient_check"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    meal_ingredient_id: Mapped[int] = mapped_column(ForeignKey("meal_ingredients.id"), nullable=False)
    checked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow_naive)

    meal_ingredient: Mapped["MealIngredient"] = relationship(back_populates="checklist_entries")
