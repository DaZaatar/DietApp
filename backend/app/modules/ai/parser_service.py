import json

from fastapi import HTTPException

from app.core.config import settings
from app.modules.ai.openrouter_client import OpenRouterClient
from app.modules.ai.prompt_service import PromptService


class ParserService:
    def __init__(self, prompt_service: PromptService, openrouter_client: OpenRouterClient) -> None:
        self.prompt_service = prompt_service
        self.openrouter_client = openrouter_client

    async def parse_meal_plan(self, raw_text: str, retries: int = 2) -> str:
        if not settings.openrouter_api_key:
            return self._fallback_parse(raw_text)

        prompt = self.prompt_service.build_meal_plan_parse_prompt(raw_text)

        last_error = None
        for _ in range(retries + 1):
            response_text = await self.openrouter_client.chat_completion(prompt)
            try:
                json.loads(response_text)
                return response_text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                prompt = (
                    f"{prompt}\n\nPrevious response was invalid JSON. "
                    "Return valid JSON only."
                )

        raise HTTPException(
            status_code=422,
            detail=f"Parser returned invalid JSON after retries: {last_error}",
        )

    def _fallback_parse(self, raw_text: str) -> str:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        meals = []
        for line in lines[:14]:
            title = line[:80]
            meals.append(
                {
                    "meal_type": "dinner",
                    "title": title,
                    "ingredients": [{"name": title.lower(), "quantity": "1", "unit": "pcs", "category": "other"}],
                }
            )

        if not meals:
            meals = [
                {
                    "meal_type": "dinner",
                    "title": "Imported meal",
                    "ingredients": [{"name": "imported meal", "quantity": "1", "unit": "pcs", "category": "other"}],
                }
            ]

        payload = {
            "name": "Imported Meal Plan (Fallback)",
            "weeks": [
                {"week_index": 1, "days": [{"day": "Monday", "meals": meals[:7]}]},
                {"week_index": 2, "days": [{"day": "Monday", "meals": meals[7:] or meals[:1]}]},
            ],
        }
        return json.dumps(payload)
