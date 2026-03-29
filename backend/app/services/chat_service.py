from app.schemas.chat import ChatRequest, ChatResponse


def preview_chat(payload: ChatRequest) -> ChatResponse:
    return ChatResponse(
        status="not_implemented",
        message="Phase 5 will retrieve grounded evidence before any generation step is introduced.",
        answer=f"Question received for future grounding workflow: {payload.question}",
    )
