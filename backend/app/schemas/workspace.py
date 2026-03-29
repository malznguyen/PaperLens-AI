from __future__ import annotations

from pydantic import BaseModel, Field


class WorkspacePaperStatus(BaseModel):
    ingested: bool
    indexed: bool


class WorkspaceSummary(BaseModel):
    total_paper_count: int = Field(ge=0)
    ingested_paper_count: int = Field(ge=0)
    indexed_paper_count: int = Field(ge=0)
    total_chunk_count: int = Field(ge=0)


class WorkspacePaper(BaseModel):
    paper_id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    primary_category: str | None = None
    status: WorkspacePaperStatus
    pdf_path: str | None = None
    parsed_path: str | None = None
    page_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    source_url: str | None = None
    collection_name: str | None = None


class WorkspaceResponse(BaseModel):
    summary: WorkspaceSummary
    papers: list[WorkspacePaper] = Field(default_factory=list)
