from pydantic import BaseModel, Field


class PaperSearchResult(BaseModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    abstract: str
    published_at: str
    updated_at: str
    categories: list[str] = Field(default_factory=list)
    pdf_url: str | None = None
    source_url: str
    primary_category: str | None = None


class SearchPapersRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    max_results: int = Field(default=10, ge=1, le=25)


class SearchPapersResponse(BaseModel):
    query: str
    count: int = Field(ge=0)
    results: list[PaperSearchResult] = Field(default_factory=list)
