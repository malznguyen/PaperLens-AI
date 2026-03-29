from app.schemas.ingest import IngestRequest, IngestResponse


def preview_ingest(payload: IngestRequest) -> IngestResponse:
    return IngestResponse(
        status="queued_placeholder",
        message="Phase 3 will download PDFs, parse content, and stage chunks for indexing.",
        accepted_count=len(payload.paper_ids),
    )
