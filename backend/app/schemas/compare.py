from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.chat import ChatCitation, RetrievedChunk, WorkflowMeta

DEFAULT_COMPARE_QUESTION = (
    "Compare these papers in terms of objective, methodology, dataset usage, "
    "strengths, limitations, and key contribution."
)
MISSING_EVIDENCE_TEXT = "Not stated in retrieved evidence."


def _normalize_paper_ids(value: Any) -> list[str]:
    if value is None:
        raise ValueError("Field is required.")
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


def _normalize_optional_question(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("Must be a string.")

    normalized = value.strip()
    return normalized or None


def _normalize_required_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required.")
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank.")
    return normalized


def _normalize_evidence_field(value: Any) -> str:
    if not isinstance(value, str):
        return MISSING_EVIDENCE_TEXT

    normalized = value.strip()
    return normalized or MISSING_EVIDENCE_TEXT


class CompareRequest(BaseModel):
    paper_ids: list[str]
    question: str | None = Field(default=None, max_length=2000)

    @field_validator("paper_ids", mode="before")
    @classmethod
    def normalize_paper_ids(cls, value: Any) -> list[str]:
        return _normalize_paper_ids(value)

    @field_validator("question", mode="before")
    @classmethod
    def normalize_question(cls, value: Any) -> str | None:
        return _normalize_optional_question(value)

    @model_validator(mode="after")
    def validate_paper_count(self) -> "CompareRequest":
        if len(self.paper_ids) < 2:
            raise ValueError("Provide at least 2 unique paper IDs for comparison.")
        if len(self.paper_ids) > 5:
            raise ValueError("Provide no more than 5 paper IDs for comparison.")
        return self

    @property
    def resolved_question(self) -> str:
        return self.question or DEFAULT_COMPARE_QUESTION


class ComparisonRow(BaseModel):
    paper_id: str
    paper_title: str
    objective: str = MISSING_EVIDENCE_TEXT
    methodology: str = MISSING_EVIDENCE_TEXT
    dataset: str = MISSING_EVIDENCE_TEXT
    strengths: str = MISSING_EVIDENCE_TEXT
    limitations: str = MISSING_EVIDENCE_TEXT
    key_contribution: str = MISSING_EVIDENCE_TEXT

    @field_validator("paper_id", "paper_title", mode="before")
    @classmethod
    def normalize_required_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator(
        "objective",
        "methodology",
        "dataset",
        "strengths",
        "limitations",
        "key_contribution",
        mode="before",
    )
    @classmethod
    def normalize_evidence_fields(cls, value: Any) -> str:
        return _normalize_evidence_field(value)


class GeneratedComparisonPayload(BaseModel):
    summary: str
    comparison_table: list[ComparisonRow] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: Any) -> str:
        return _normalize_required_text(value, "summary")

    @field_validator("citations", mode="before")
    @classmethod
    def normalize_citations(cls, value: Any) -> list[str]:
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


class CompareResponse(BaseModel):
    status: Literal["completed", "partial"]
    summary: str | None = None
    comparison_table: list[ComparisonRow] = Field(default_factory=list)
    citations: list[ChatCitation] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    meta: WorkflowMeta | None = None
    message: str
