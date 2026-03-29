from __future__ import annotations

from pathlib import Path

import fitz
import httpx

from app.core.config import Settings, get_settings
from app.schemas.ingest import IngestRequest, ParsedPage, ParsedPaperDocument
from app.utils.file_utils import repo_relative_path
from app.utils.text_utils import count_words


class PdfDownloadError(RuntimeError):
    """Raised when a PDF cannot be downloaded."""


class PdfTimeoutError(PdfDownloadError):
    """Raised when a PDF download times out."""


class InvalidPdfError(PdfDownloadError):
    """Raised when downloaded content does not look like a PDF."""


class PdfParseError(RuntimeError):
    """Raised when PDF text extraction fails."""


class PdfService:
    def __init__(
        self,
        settings: Settings | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._settings = settings or get_settings()
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 10.0))
        self._headers = {
            "Accept": "application/pdf",
            "User-Agent": "PaperLens-AI/0.1",
        }

    async def download_pdf(self, pdf_url: str) -> bytes:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                headers=self._headers,
                follow_redirects=True,
            ) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise PdfTimeoutError("Timed out while downloading the PDF.") from exc
        except httpx.HTTPStatusError as exc:
            raise PdfDownloadError("Failed to download the PDF.") from exc
        except httpx.HTTPError as exc:
            raise PdfDownloadError("Failed to download the PDF.") from exc

        pdf_bytes = response.content
        if not pdf_bytes:
            raise InvalidPdfError("Downloaded PDF is empty.")

        content_type = response.headers.get("content-type", "")
        if not _looks_like_pdf(content_type=content_type, content=pdf_bytes):
            raise InvalidPdfError("Downloaded content is not a valid PDF.")

        return pdf_bytes

    def parse_pdf(self, pdf_path: Path, payload: IngestRequest) -> ParsedPaperDocument:
        document = None

        try:
            document = fitz.open(str(pdf_path))
        except Exception as exc:
            raise PdfParseError("Failed to open the downloaded PDF.") from exc

        try:
            pages: list[ParsedPage] = []
            page_texts: list[str] = []

            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()
                pages.append(ParsedPage(page_number=page_number, text=text))
                page_texts.append(text)

            page_count = document.page_count
        except Exception as exc:
            raise PdfParseError("Failed to parse text from the PDF.") from exc
        finally:
            if document is not None:
                document.close()

        full_text = "\n\n".join(text for text in page_texts if text).strip()
        if not full_text:
            raise PdfParseError("The PDF was parsed but no text could be extracted.")

        return ParsedPaperDocument(
            paper_id=payload.id,
            title=payload.title,
            authors=payload.authors,
            abstract=payload.abstract,
            published_at=payload.published_at,
            updated_at=payload.updated_at,
            categories=payload.categories,
            primary_category=payload.primary_category,
            source_url=payload.source_url,
            pdf_url=payload.pdf_url,
            pdf_path=repo_relative_path(pdf_path),
            page_count=page_count,
            character_count=len(full_text),
            word_count=count_words(full_text),
            pages=pages,
            full_text=full_text,
        )


def _looks_like_pdf(content_type: str, content: bytes) -> bool:
    return "pdf" in content_type.lower() or content.lstrip().startswith(b"%PDF-")
