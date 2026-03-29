from pydantic import BaseModel, Field


class PaperSearchResult(BaseModel):
    id: str
    title: str
    abstract: str
    authors: list[str]
    source_url: str
    pdf_url: str | None = None


class SearchPapersRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    max_results: int = Field(default=10, ge=1, le=25)


class SearchPapersResponse(BaseModel):
    query: str
    status: str
    message: str
    papers: list[PaperSearchResult] = Field(default_factory=list)
