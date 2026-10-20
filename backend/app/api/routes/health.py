from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings
from app.database.readiness import database_readiness_response

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="healthy", version=settings.app_version)


@router.get("/ready")
async def readiness():
    return database_readiness_response()
