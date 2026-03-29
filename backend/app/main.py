from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from starlette.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)


@app.exception_handler(OperationalError)
async def sqlalchemy_operational_error_handler(_request, _exc: OperationalError):
    """Surface DB/schema issues as JSON instead of an opaque 500 (e.g. missing tables before `alembic upgrade head`)."""
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Database error (often missing or outdated schema). From the backend directory run: "
                "alembic upgrade head"
            ),
        },
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


_static = Path(settings.static_root) if settings.static_root else None
if _static is not None and _static.is_dir():
    app.mount("/", StaticFiles(directory=str(_static), html=True), name="spa")
