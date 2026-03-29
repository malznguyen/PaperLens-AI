from fastapi import APIRouter, status

from app.schemas.ingest import IngestRequest, IngestResponse
from app.services.ingest_service import preview_ingest

router = APIRouter(prefix="/ingest")


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Phase 3 ingestion placeholder",
)
def ingest_papers(payload: IngestRequest) -> IngestResponse:
    return preview_ingest(payload)
