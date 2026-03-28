SYSTEM_PROMPT = """
You convert raw meal-plan text into strict JSON.
Return valid JSON only, no markdown.
Schema:
{
  "name": string,
  "weeks": [
    {
      "week_index": number,
      "days": [
        {
          "day": string,
          "meals": [
            {
              "meal_type": string,
              "title": string,
              "ingredients": [
                {"name": string, "quantity": string, "unit": string, "category": string}
              ]
            }
          ]
        }
      ]
    }
  ]
}
Rules:
- Always provide exactly 2 weeks when input is bi-weekly.
- Normalize meal_type to breakfast|lunch|dinner|snack.
- Keep food titles concise.
- Include realistic ingredient quantities and units for each meal.
- quantity must be numeric text (for example 1, 1.5, 0.25).
- unit must be a standard unit (for example g, kg, ml, l, tsp, tbsp, cup, pcs).
- category must be exactly one of: meats|dairy|bread|grains|fruits|vegetables|fats|spices|nuts|other.
  Use meats for poultry, beef, fish, eggs; bread for loaves, buns, flatbread; grains for rice, pasta, oats, legumes;
  vegetables and fruits as usual; dairy for milk, cheese, yogurt; fats for oils, butter; spices for herbs and spices;
  nuts for nuts and seeds; other only when nothing else fits.
- Group ingredients logically by category and assign each ingredient exactly one category.
- Ingredient names may appear in Arabic but transliterated into Latin letters and digits (Arabizi style), for example
  "7abach" or "7abash" meaning turkey, or similar. Recognize common North African / Levantine food spellings,
  normalize the displayed ingredient name to clear English (e.g. turkey) while preserving quantities and units from the source.
Examples of good category assignments:
- "500 g chicken thighs" -> meats; "250 ml milk" -> dairy; "2 slices bread" -> bread; "80 g oats" -> grains;
- "1 apple" -> fruits; "200 g tomatoes" -> vegetables; "30 ml olive oil" -> fats; "1 tsp cumin" -> spices.
""".strip()


class PromptService:
    def build_meal_plan_parse_prompt(self, source_text: str) -> str:
        return f"{SYSTEM_PROMPT}\n\nInput:\n{source_text}"
