from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import preview_chat

router = APIRouter(prefix="/chat")


@router.post("", response_model=ChatResponse, summary="Phase 5 grounded chat placeholder")
def research_chat(payload: ChatRequest) -> ChatResponse:
    return preview_chat(payload)
