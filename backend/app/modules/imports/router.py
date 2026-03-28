from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.ai.openrouter_client import OpenRouterClient
from app.modules.ai.parser_service import ParserService
from app.modules.ai.prompt_service import PromptService
from app.modules.imports.meal_plan_import_service import MealPlanImportService
from app.modules.imports.pdf_extractor import PDFExtractor
from app.modules.imports.schemas import ImportResult, MealPlanImportPreview
from app.modules.meal_plans.service import persist_imported_meal_plan

router = APIRouter()

pdf_extractor = PDFExtractor()
prompt_service = PromptService()
openrouter_client = OpenRouterClient()
parser_service = ParserService(prompt_service, openrouter_client)
import_service = MealPlanImportService(parser_service)


@router.post("/preview", response_model=MealPlanImportPreview)
async def preview_import(file: UploadFile = File(...)):
    text = await pdf_extractor.extract_text(file)
    return await import_service.parse_pdf_text(text)


@router.post("/commit", response_model=ImportResult)
def commit_import(payload: MealPlanImportPreview, db: Session = Depends(get_db)):
    meal_plan = persist_imported_meal_plan(db, payload.model_dump())
    return ImportResult(meal_plan_id=meal_plan.id, name=meal_plan.name)
