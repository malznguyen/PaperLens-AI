from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.synthesis import TopicSynthesisResponse
from app.services.synthesis_service import (
    SynthesisEvidenceError,
    SynthesisNotReadyError,
    SynthesisService,
    SynthesisServiceError,
    SynthesisValidationError,
    get_synthesis_service,
)

router = APIRouter(prefix="/summarize-topic")


@router.post(
    "",
    response_model=TopicSynthesisResponse,
    summary="Generate a grounded topic synthesis or literature overview from indexed papers",
)
async def summarize_topic(
    payload: dict[str, Any],
    service: SynthesisService = Depends(get_synthesis_service),
) -> TopicSynthesisResponse:
    try:
        return await service.summarize_topic(payload)
    except SynthesisValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SynthesisNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SynthesisEvidenceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except SynthesisServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
