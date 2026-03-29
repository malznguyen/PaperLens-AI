from pydantic import BaseModel, Field


class CitationPreview(BaseModel):
    paper_id: str
    snippet: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    paper_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    status: str
    message: str
    answer: str | None = None
    citations: list[CitationPreview] = Field(default_factory=list)
