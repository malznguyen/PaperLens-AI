from app.schemas.compare import CompareDimension, CompareRequest, CompareResponse


def preview_compare(payload: CompareRequest) -> CompareResponse:
    dimensions = [
        CompareDimension(
            label="Methodology",
            summary="Comparison workflow will normalize study design details once ingestion and retrieval are available.",
        ),
        CompareDimension(
            label="Evidence traceability",
            summary="Every future comparison row will link back to retrieved chunks and paper metadata.",
        ),
    ]
    return CompareResponse(
        status="not_implemented",
        message=f"Phase 6 will compare {len(payload.paper_ids)} ingested papers with grounded criteria.",
        dimensions=dimensions,
    )
