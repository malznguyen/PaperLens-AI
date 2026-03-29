from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class IndexPaperRequest(BaseModel):
    paper_id: str

    @field_validator("paper_id", mode="before")
    @classmethod
    def normalize_paper_id(cls, value: Any) -> str:
        if value is None:
            raise ValueError("Field is required.")
        if not isinstance(value, str):
            raise ValueError("Must be a string.")

        normalized = value.strip()
        if not normalized:
            raise ValueError("Must not be blank.")
        return normalized


class IndexedChunk(BaseModel):
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
    content_hash: str
    start_word_index: int = Field(ge=0)
    end_word_index: int = Field(ge=0)

    def to_chroma_metadata(self) -> dict[str, str | int]:
        return {
            "paper_id": self.paper_id,
            "paper_title": self.paper_title,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "page_chunk_index": self.page_chunk_index,
            "source_url": self.source_url,
            "pdf_path": self.pdf_path,
            "word_count": self.word_count,
            "content_hash": self.content_hash,
            "start_word_index": self.start_word_index,
            "end_word_index": self.end_word_index,
        }


class IndexPaperResponse(BaseModel):
    paper_id: str
    status: Literal["completed", "cached"]
    chunk_count: int = Field(ge=0)
    collection_name: str
    message: str


class IndexCacheRecord(BaseModel):
    paper_id: str
    content_hash: str
    chunk_count: int = Field(ge=0)
    collection_name: str
