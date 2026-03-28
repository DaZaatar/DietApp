export type ParsedIngredient = {
  name: string;
  quantity: string;
  unit: string;
  category: string;
};

export type ParsedMeal = {
  meal_type: string;
  title: string;
  ingredients: ParsedIngredient[];
};

export type ParsedDay = {
  day: string;
  meals: ParsedMeal[];
};

export type ParsedWeek = {
  week_index: number;
  days: ParsedDay[];
};

export type MealPlanPreview = {
  name: string;
  weeks: ParsedWeek[];
};
