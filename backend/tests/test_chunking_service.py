from app.schemas.ingest import ParsedPage, ParsedPaperDocument
from app.services.chunking_service import ChunkingService
from app.utils.text_utils import count_words


def build_document(page_texts: list[str]) -> ParsedPaperDocument:
    full_text = "\n\n".join(text.strip() for text in page_texts if text.strip())
    return ParsedPaperDocument(
        paper_id="2401.12345",
        title="Page Aware Chunking Test Paper",
        authors=["Alice Smith"],
        abstract="Chunking service test fixture.",
        published_at="2024-01-10T12:00:00Z",
        updated_at="2024-01-15T09:30:00Z",
        categories=["cs.CL"],
        primary_category="cs.CL",
        source_url="https://arxiv.org/abs/2401.12345",
        pdf_url="https://arxiv.org/pdf/2401.12345.pdf",
        pdf_path="backend/data/raw_pdfs/2401.12345.pdf",
        page_count=len(page_texts),
        character_count=len(full_text),
        word_count=count_words(full_text),
        pages=[
            ParsedPage(page_number=index, text=text)
            for index, text in enumerate(page_texts, start=1)
        ],
        full_text=full_text,
    )


def test_chunking_service_splits_long_pages_skips_empty_pages_and_preserves_provenance() -> None:
    service = ChunkingService(chunk_size_words=6, chunk_overlap_words=2)
    document = build_document(
        [
            "alpha beta gamma delta epsilon zeta eta theta iota kappa",
            "   ",
            "lambda mu nu xi",
        ]
    )

    chunks = service.chunk_document(document, content_hash="paper-hash")

    assert len(chunks) == 3
    assert [chunk.page_number for chunk in chunks] == [1, 1, 3]
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert [chunk.page_chunk_index for chunk in chunks] == [0, 1, 0]
    assert chunks[0].paper_id == document.paper_id
    assert chunks[0].paper_title == document.title
    assert chunks[0].source_url == document.source_url
    assert chunks[0].pdf_path == document.pdf_path
    assert chunks[0].start_word_index == 0
    assert chunks[0].end_word_index == 6
    assert chunks[1].start_word_index == 4
    assert chunks[1].end_word_index == 10
    assert chunks[2].word_count == 4
    assert all("  " not in chunk.text for chunk in chunks)


def test_chunking_service_generates_deterministic_chunk_ids_for_same_document() -> None:
    service = ChunkingService(chunk_size_words=5, chunk_overlap_words=1)
    document = build_document(
        [
            "alpha beta gamma delta epsilon zeta eta theta",
        ]
    )

    first_chunks = service.chunk_document(document, content_hash="paper-hash")
    second_chunks = service.chunk_document(document, content_hash="paper-hash")

    assert [chunk.chunk_id for chunk in first_chunks] == [
        chunk.chunk_id for chunk in second_chunks
    ]
