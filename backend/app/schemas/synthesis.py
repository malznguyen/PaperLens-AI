from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.chat import ChatCitation, RetrievedChunk, WorkflowMeta
from app.schemas.compare import _normalize_optional_question, _normalize_paper_ids, _normalize_required_text

DEFAULT_SYNTHESIS_TOPIC = "Selected indexed papers"
DEFAULT_SYNTHESIS_QUERY = (
    "Synthesize the selected papers with attention to recurring themes, methodology "
    "trends, open challenges, research gaps, and future directions."
)


def _normalize_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings.")

    normalized_values: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} must be a list of strings.")

        normalized = item.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            normalized_values.append(normalized)

    return normalized_values


class TopicSynthesisRequest(BaseModel):
    topic: str | None = Field(default=None, max_length=500)
    paper_ids: list[str] = Field(default_factory=list)

    @field_validator("topic", mode="before")
    @classmethod
    def normalize_topic(cls, value: Any) -> str | None:
        return _normalize_optional_question(value)

    @field_validator("paper_ids", mode="before")
    @classmethod
    def normalize_paper_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        return _normalize_paper_ids(value)

    @model_validator(mode="after")
    def validate_request(self) -> "TopicSynthesisRequest":
        if not self.topic and not self.paper_ids:
            raise ValueError("Provide a topic, one or more paper IDs, or both.")
        return self

    @property
    def display_topic(self) -> str:
        return self.topic or DEFAULT_SYNTHESIS_TOPIC

    @property
    def retrieval_query(self) -> str:
        if self.topic:
            return (
                f"{self.topic}. Focus on recurring themes, methodological trends, "
                "open challenges, research gaps, and future directions."
            )
        return DEFAULT_SYNTHESIS_QUERY


class GeneratedSynthesisPayload(BaseModel):
    topic: str
    overview: str
    themes: list[str] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)
    open_challenges: list[str] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)
    future_directions: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False

    @field_validator("topic", "overview", mode="before")
    @classmethod
    def normalize_required_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator(
        "themes",
        "trends",
        "open_challenges",
        "research_gaps",
        "future_directions",
        "citations",
        mode="before",
    )
    @classmethod
    def normalize_list_fields(cls, value: Any, info) -> list[str]:
        return _normalize_string_list(value, info.field_name)


class TopicSynthesisResponse(BaseModel):
    status: Literal["completed", "partial"]
    topic: str
    overview: str | None = None
    themes: list[str] = Field(default_factory=list)
    trends: list[str] = Field(default_factory=list)
    open_challenges: list[str] = Field(default_factory=list)
    research_gaps: list[str] = Field(default_factory=list)
    future_directions: list[str] = Field(default_factory=list)
    citations: list[ChatCitation] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    meta: WorkflowMeta | None = None
    message: str
