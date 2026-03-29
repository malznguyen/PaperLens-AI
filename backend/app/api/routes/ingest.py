from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.ingest import IngestResponse
from app.services.ingest_service import (
    IngestProcessingError,
    IngestService,
    IngestStorageError,
    IngestTimeoutError,
    IngestUpstreamError,
    IngestValidationError,
    get_ingest_service,
)

router = APIRouter(prefix="/ingest")


@router.post(
    "",
    response_model=IngestResponse,
    summary="Download and parse a selected paper PDF",
)
async def ingest_paper(
    payload: dict[str, Any],
    service: IngestService = Depends(get_ingest_service),
) -> IngestResponse:
    try:
        return await service.ingest_paper(payload)
    except IngestValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IngestTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    except IngestUpstreamError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except IngestProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except IngestStorageError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
