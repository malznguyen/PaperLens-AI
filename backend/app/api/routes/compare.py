from fastapi import APIRouter

from app.schemas.compare import CompareRequest, CompareResponse
from app.services.compare_service import preview_compare

router = APIRouter(prefix="/compare")


@router.post("", response_model=CompareResponse, summary="Phase 6 comparison placeholder")
def compare_papers(payload: CompareRequest) -> CompareResponse:
    return preview_compare(payload)
