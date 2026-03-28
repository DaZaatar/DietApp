import json

from fastapi import HTTPException

from app.modules.ai.parser_service import ParserService
from app.modules.imports.schemas import MealPlanImportPreview


class MealPlanImportService:
    def __init__(self, parser_service: ParserService) -> None:
        self.parser_service = parser_service

    async def parse_pdf_text(self, text: str) -> MealPlanImportPreview:
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text extracted from PDF")

        parsed_json = await self.parser_service.parse_meal_plan(text)

        try:
            payload = json.loads(parsed_json)
            return MealPlanImportPreview.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=422, detail=f"Invalid parsed meal plan JSON: {exc}") from exc
