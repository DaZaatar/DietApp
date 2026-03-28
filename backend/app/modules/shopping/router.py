from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db.session import get_db
from app.modules.shopping.schemas import ShoppingChecklistUpdate, ShoppingListResponse
from app.modules.shopping.service import ShoppingService

router = APIRouter()
service = ShoppingService()


@router.get("/list", response_model=ShoppingListResponse)
def get_shopping_list(
    meal_plan_id: int | None = None,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return service.list_for_user(db, user_id=user_id, meal_plan_id=meal_plan_id)


@router.patch("/items/{ingredient_id}")
def update_shopping_item_check(
    ingredient_id: str,
    payload: ShoppingChecklistUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    service.set_group_checked(
        db,
        user_id=user_id,
        meal_plan_id=payload.meal_plan_id,
        item_key=ingredient_id,
        checked=payload.checked,
    )
    return {"ok": True}
