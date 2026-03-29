from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    paper_ids: list[str] = Field(min_length=1)


class IngestResponse(BaseModel):
    status: str
    message: str
    accepted_count: int
