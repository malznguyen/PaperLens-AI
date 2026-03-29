from __future__ import annotations

from typing import Any, Literal

from pydantic import AnyHttpUrl, BaseModel, Field, TypeAdapter, ValidationInfo, field_validator

http_url_adapter = TypeAdapter(AnyHttpUrl)


class IngestRequest(BaseModel):
    id: str
    title: str
    pdf_url: str
    source_url: str
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    categories: list[str] = Field(default_factory=list)
    primary_category: str | None = None

    @field_validator("id", "title", "pdf_url", "source_url", mode="before")
    @classmethod
    def normalize_required_string(cls, value: Any) -> str:
        if value is None:
            raise ValueError("Field is required.")
        if not isinstance(value, str):
            raise ValueError("Must be a string.")

        normalized = value.strip()
        if not normalized:
            raise ValueError("Must not be blank.")
        return normalized

    @field_validator("abstract", "published_at", "updated_at", "primary_category", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Must be a string.")

        normalized = value.strip()
        return normalized or None

    @field_validator("authors", "categories", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Must be a list of strings.")

        normalized_items: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("All values must be strings.")

            normalized = item.strip()
            if normalized:
                normalized_items.append(normalized)

        return normalized_items

    @field_validator("pdf_url", "source_url")
    @classmethod
    def validate_http_url(cls, value: str, info: ValidationInfo) -> str:
        try:
            http_url_adapter.validate_python(value)
        except Exception as exc:  # pragma: no cover - Pydantic raises multiple validation types.
            raise ValueError(f"{info.field_name} must be a valid HTTP or HTTPS URL.") from exc
        return value


class ParsedPage(BaseModel):
    page_number: int = Field(ge=1)
    text: str


class ParsedPaperDocument(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    categories: list[str] = Field(default_factory=list)
    primary_category: str | None = None
    source_url: str
    pdf_url: str
    pdf_path: str
    page_count: int = Field(ge=0)
    character_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    pages: list[ParsedPage] = Field(default_factory=list)
    full_text: str


class IngestResponse(BaseModel):
    paper_id: str
    status: Literal["completed", "cached"]
    pdf_path: str
    parsed_path: str
    page_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    message: str
