from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings
from app.schemas.health import HealthResponse
from app.services.health_service import build_health_response

router = APIRouter(prefix="/health")


@router.get("", response_model=HealthResponse, summary="Backend health check")
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return build_health_response(settings)
