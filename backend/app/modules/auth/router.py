from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.deps import get_session_user_id_strict
from app.db.session import get_db
from app.modules.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, UserPublic
from app.modules.auth.service import authenticate, create_access_token, register_user
from app.modules.models import User

router = APIRouter()

COOKIE_NAME = "access_token"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days when remember_me


@router.post("/register", response_model=UserPublic)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, email=str(payload.email), password=payload.password)
    return UserPublic(id=user.id, email=user.email)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate(db, email=str(payload.email), password=payload.password)
    token = create_access_token(user.id)
    max_age = SESSION_MAX_AGE if payload.remember_me else None
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=max_age,
        path="/",
    )
    return LoginResponse(user_id=user.id, email=user.email)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserPublic)
def read_me(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_session_user_id_strict),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return UserPublic(id=user.id, email=user.email)
