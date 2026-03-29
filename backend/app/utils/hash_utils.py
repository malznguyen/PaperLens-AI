from __future__ import annotations

import hashlib
import json

from app.schemas.ingest import ParsedPaperDocument
from app.utils.chunk_utils import normalize_whitespace


def compute_parsed_document_hash(document: ParsedPaperDocument) -> str:
    normalized_pages = [
        {
            "page_number": page.page_number,
            "text": normalize_whitespace(page.text),
        }
        for page in document.pages
        if normalize_whitespace(page.text)
    ]

    payload = {
        "paper_id": document.paper_id,
        "title": normalize_whitespace(document.title),
        "source_url": document.source_url,
        "pdf_url": document.pdf_url,
        "page_count": document.page_count,
        "pages": normalized_pages,
        "full_text": normalize_whitespace(document.full_text),
    }

    serialized_payload = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()


def build_chunk_id(
    paper_id: str,
    page_number: int,
    chunk_index: int,
    text: str,
) -> str:
    normalized_text = normalize_whitespace(text)
    suffix = hashlib.sha256(
        f"{paper_id}|{page_number}|{chunk_index}|{normalized_text}".encode("utf-8")
    ).hexdigest()[:12]
    return f"{paper_id}-p{page_number:04d}-c{chunk_index:04d}-{suffix}"
