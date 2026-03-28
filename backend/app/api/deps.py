from fastapi import Cookie, Header, HTTPException

from app.core.config import settings
from app.modules.auth.service import decode_user_id


def _token_from_authorization(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token:
            return token
    return None


def get_session_user_id_strict(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
) -> int:
    """Requires Bearer token or HttpOnly access_token cookie (no dev default user)."""
    bearer = _token_from_authorization(authorization)
    if bearer:
        return decode_user_id(bearer)
    if access_token:
        return decode_user_id(access_token)
    raise HTTPException(status_code=401, detail="Not authenticated")


def get_current_user_id(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> int:
    bearer = _token_from_authorization(authorization)
    if bearer:
        return decode_user_id(bearer)
    if access_token:
        return decode_user_id(access_token)
    if settings.allow_dev_user_header and x_user_id is not None:
        return x_user_id
    if settings.allow_default_user:
        return 1
    raise HTTPException(status_code=401, detail="Not authenticated")
