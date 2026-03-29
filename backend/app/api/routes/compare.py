from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.compare import CompareResponse
from app.services.compare_service import (
    CompareEvidenceError,
    CompareNotReadyError,
    CompareService,
    CompareServiceError,
    CompareValidationError,
    get_compare_service,
)

router = APIRouter(prefix="/compare")


@router.post(
    "",
    response_model=CompareResponse,
    summary="Compare 2 to 5 indexed papers with grounded evidence and citations",
)
async def compare_papers(
    payload: dict[str, Any],
    service: CompareService = Depends(get_compare_service),
) -> CompareResponse:
    try:
        return await service.compare_papers(payload)
    except CompareValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except CompareNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CompareEvidenceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except CompareServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
