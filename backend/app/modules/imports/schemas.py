from pydantic import BaseModel, Field


class ParsedIngredient(BaseModel):
    name: str
    quantity: str = Field(..., examples=["1.5", "2", "0.5"])
    unit: str = Field(..., examples=["kg", "g", "pcs", "tbsp", "cup"])
    category: str = Field(
        default="other",
        examples=["meats", "dairy", "bread", "grains", "fruits", "vegetables", "fats", "spices", "nuts", "other"],
    )


class ParsedMeal(BaseModel):
    meal_type: str = Field(..., examples=["breakfast", "lunch", "dinner", "snack"])
    title: str
    ingredients: list[ParsedIngredient] = Field(default_factory=list)


class ParsedDay(BaseModel):
    day: str
    meals: list[ParsedMeal]


class ParsedWeek(BaseModel):
    week_index: int
    days: list[ParsedDay]


class MealPlanImportPreview(BaseModel):
    name: str
    weeks: list[ParsedWeek]


class ImportResult(BaseModel):
    meal_plan_id: int
    name: str
