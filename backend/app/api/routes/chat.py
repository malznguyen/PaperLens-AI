from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.chat import ChatResponse
from app.services.chat_service import (
    ChatEvidenceError,
    ChatNotReadyError,
    ChatService,
    ChatServiceError,
    ChatValidationError,
    get_chat_service,
)

router = APIRouter(prefix="/chat")


@router.post(
    "",
    response_model=ChatResponse,
    summary="Retrieve grounded evidence from indexed papers and generate a cited answer",
)
async def research_chat(
    payload: dict[str, Any],
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    try:
        return await service.answer_question(payload)
    except ChatValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ChatNotReadyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ChatEvidenceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ChatServiceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
