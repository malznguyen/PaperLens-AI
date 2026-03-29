from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    paper_ids: list[str] = Field(min_length=2, max_length=5)


class CompareDimension(BaseModel):
    label: str
    summary: str


class CompareResponse(BaseModel):
    status: str
    message: str
    dimensions: list[CompareDimension] = Field(default_factory=list)
