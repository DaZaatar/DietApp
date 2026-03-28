from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.imports.router import router as imports_router
from app.modules.meal_plans.router import router as meal_plans_router
from app.modules.shopping.router import router as shopping_router
from app.modules.tracking.router import router as tracking_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(imports_router, prefix="/imports", tags=["imports"])
api_router.include_router(tracking_router, prefix="/tracking", tags=["tracking"])
api_router.include_router(shopping_router, prefix="/shopping", tags=["shopping"])
api_router.include_router(meal_plans_router, prefix="/meal-plans", tags=["meal-plans"])
