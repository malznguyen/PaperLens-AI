from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(max_length=2000)
    paper_ids: list[str] = Field(default_factory=list)
    top_k: int | None = None

    @field_validator("question", mode="before")
    @classmethod
    def normalize_question(cls, value: Any) -> str:
        if value is None:
            raise ValueError("Field is required.")
        if not isinstance(value, str):
            raise ValueError("Must be a string.")

        normalized = value.strip()
        if not normalized:
            raise ValueError("Must not be blank.")
        return normalized

    @field_validator("paper_ids", mode="before")
    @classmethod
    def normalize_paper_ids(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Must be a list of strings.")

        normalized_ids: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str):
                raise ValueError("All values must be strings.")

            normalized = item.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                normalized_ids.append(normalized)

        return normalized_ids

    @field_validator("top_k", mode="before")
    @classmethod
    def normalize_top_k(cls, value: Any) -> int | None:
        if value in (None, ""):
            return None
        if isinstance(value, bool):
            raise ValueError("Must be an integer.")

        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Must be an integer.") from exc


class RetrievedChunk(BaseModel):
    label: str | None = None
    chunk_id: str
    paper_id: str
    paper_title: str
    page_number: int = Field(ge=1)
    chunk_index: int = Field(ge=0)
    page_chunk_index: int = Field(ge=0)
    source_url: str
    pdf_path: str
    text: str
    word_count: int = Field(ge=0)
    start_word_index: int = Field(ge=0)
    end_word_index: int = Field(ge=0)
    similarity_score: float | None = None


class ChatCitation(BaseModel):
    label: str
    paper_id: str
    paper_title: str
    page_number: int = Field(ge=1)
    chunk_id: str
    source_url: str


class GeneratedAnswerPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    answer: str
    citation_labels: list[str] = Field(default_factory=list, alias="citations")
    insufficient_evidence: bool = False

    @field_validator("answer", mode="before")
    @classmethod
    def normalize_answer(cls, value: Any) -> str:
        if value is None:
            raise ValueError("answer is required.")
        if not isinstance(value, str):
            raise ValueError("answer must be a string.")

        normalized = value.strip()
        if not normalized:
            raise ValueError("answer must not be blank.")
        return normalized

    @field_validator("citation_labels", mode="before")
    @classmethod
    def normalize_citation_labels(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("citations must be a list of strings.")

        normalized_labels: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str):
                raise ValueError("citations must be a list of strings.")

            normalized = item.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                normalized_labels.append(normalized)

        return normalized_labels


class GenerationResult(BaseModel):
    answer: str
    citation_labels: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
    model: str | None = None


class WorkflowMeta(BaseModel):
    retrieval_ms: int = Field(ge=0)
    reranking_ms: int = Field(default=0, ge=0)
    generation_ms: int = Field(default=0, ge=0)
    total_ms: int = Field(ge=0)
    retrieved_chunk_count: int = Field(ge=0)
    citation_count: int = Field(ge=0)
    status: Literal["completed", "partial", "failed"]


class ChatResponse(BaseModel):
    status: Literal["completed", "partial"]
    question: str
    answer: str | None = None
    citations: list[ChatCitation] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    meta: WorkflowMeta | None = None
    message: str
