from __future__ import annotations

import asyncio
import logging
import re
import xml.etree.ElementTree as ET

import httpx

from app.core.config import get_settings
from app.schemas.search import PaperSearchResult

ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"
ARXIV_NAMESPACE = "http://arxiv.org/schemas/atom"
NAMESPACES = {
    "atom": ATOM_NAMESPACE,
    "arxiv": ARXIV_NAMESPACE,
}
WHITESPACE_RE = re.compile(r"\s+")
LOG_BODY_PREVIEW_LIMIT = 240
ARXIV_ID_RE = re.compile(
    r"(?P<identifier>(?:[a-z.\-]+/[0-9]{7}|[0-9]{4}\.[0-9]{4,5}))(?:v[0-9]+)?(?:\.pdf)?$",
    re.IGNORECASE,
)
logger = logging.getLogger(__name__)


class ArxivServiceError(RuntimeError):
    """Raised when the arXiv API cannot be queried or parsed."""


class ArxivService:
    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
    ) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.arxiv_base_url
        self.timeout = httpx.Timeout(timeout_seconds)
        self.max_retries = max_retries
        self._logger = logger
        self.headers = {
            "Accept": "application/atom+xml",
            "User-Agent": "PaperLens-AI/0.1 (mailto:paperlens-ai@users.noreply.github.com)",
        }

    async def search_papers(self, query: str, max_results: int) -> list[PaperSearchResult]:
        feed_xml = await self._fetch_feed(query=query, max_results=max_results)
        return self._parse_feed(feed_xml)

    async def _fetch_feed(self, query: str, max_results: int) -> str:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
        }

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=True,
        ) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    request = client.build_request("GET", self.base_url, params=params)
                    response = await client.send(request)
                    response.raise_for_status()
                    return response.text
                except httpx.HTTPStatusError as exc:
                    if self._should_retry_status(exc.response.status_code, attempt):
                        self._log_status_error(exc, attempt=attempt, will_retry=True)
                        if exc.response.status_code == 429:
                            retry_after = exc.response.headers.get("retry-after")
                            delay = float(retry_after) if retry_after else 3.0
                        else:
                            delay = 1.0 * (attempt + 1)
                        await asyncio.sleep(delay)
                        continue
                    self._log_status_error(exc, attempt=attempt, will_retry=False)
                    raise ArxivServiceError("arXiv returned an unexpected response.") from exc
                except httpx.HTTPError as exc:
                    if attempt < self.max_retries:
                        self._log_transport_error(exc, attempt=attempt, will_retry=True)
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
                    self._log_transport_error(exc, attempt=attempt, will_retry=False)
                    raise ArxivServiceError("arXiv request failed.") from exc

        raise ArxivServiceError("arXiv request failed.")

    def _parse_feed(self, feed_xml: str) -> list[PaperSearchResult]:
        try:
            root = ET.fromstring(feed_xml)
        except ET.ParseError as exc:
            raise ArxivServiceError("Failed to parse the arXiv response.") from exc

        return [self._parse_entry(entry) for entry in root.findall("atom:entry", NAMESPACES)]

    def _parse_entry(self, entry: ET.Element) -> PaperSearchResult:
        entry_id = _extract_text(entry, "atom:id")
        source_url = self._extract_source_url(entry) or entry_id
        paper_id = _extract_arxiv_id(source_url or entry_id)
        title = _normalize_whitespace(_extract_text(entry, "atom:title"))

        if not paper_id:
            paper_id = source_url or title

        return PaperSearchResult(
            id=paper_id,
            title=title,
            authors=self._extract_authors(entry),
            abstract=_normalize_whitespace(_extract_text(entry, "atom:summary")),
            published_at=_extract_text(entry, "atom:published"),
            updated_at=_extract_text(entry, "atom:updated"),
            categories=self._extract_categories(entry),
            pdf_url=self._extract_pdf_url(entry, source_url),
            source_url=source_url,
            primary_category=self._extract_primary_category(entry),
        )

    def _extract_authors(self, entry: ET.Element) -> list[str]:
        authors: list[str] = []

        for author in entry.findall("atom:author", NAMESPACES):
            name = author.find("atom:name", NAMESPACES)
            normalized_name = _normalize_whitespace(name.text if name is not None else "")
            if normalized_name:
                authors.append(normalized_name)

        return authors

    def _extract_categories(self, entry: ET.Element) -> list[str]:
        categories: list[str] = []

        for category in entry.findall("atom:category", NAMESPACES):
            term = category.get("term")
            if term and term not in categories:
                categories.append(term)

        return categories

    def _extract_primary_category(self, entry: ET.Element) -> str | None:
        category = entry.find("arxiv:primary_category", NAMESPACES)
        if category is None:
            return None
        return category.get("term")

    def _extract_source_url(self, entry: ET.Element) -> str:
        for link in entry.findall("atom:link", NAMESPACES):
            href = link.get("href")
            if link.get("rel") == "alternate" and href:
                return href

        return ""

    def _extract_pdf_url(self, entry: ET.Element, source_url: str) -> str | None:
        for link in entry.findall("atom:link", NAMESPACES):
            href = link.get("href")
            if href and (link.get("title") == "pdf" or href.endswith(".pdf")):
                return href

        if source_url and "/abs/" in source_url:
            return f"{source_url.replace('/abs/', '/pdf/')}.pdf"

        return None

    def _should_retry_status(self, status_code: int, attempt: int) -> bool:
        return attempt < self.max_retries and (status_code == 429 or status_code >= 500)

    def _log_status_error(
        self,
        exc: httpx.HTTPStatusError,
        *,
        attempt: int,
        will_retry: bool,
    ) -> None:
        response = exc.response
        response_request = response.request
        log_message = (
            "Retrying arXiv request after upstream HTTP error."
            if will_retry
            else "arXiv request failed with upstream HTTP error."
        )
        log_method = self._logger.warning if will_retry else self._logger.error
        log_method(
            "%s status=%s request_url=%s response_url=%s redirect_location=%s attempt=%s/%s body_preview=%r",
            log_message,
            response.status_code,
            str(response_request.url),
            str(response.url),
            response.headers.get("location"),
            attempt + 1,
            self.max_retries + 1,
            _preview_text(response.text),
        )

    def _log_transport_error(
        self,
        exc: httpx.HTTPError,
        *,
        attempt: int,
        will_retry: bool,
    ) -> None:
        request = getattr(exc, "request", None)
        request_url = str(request.url) if request is not None else self.base_url
        log_message = (
            "Retrying arXiv request after transport error."
            if will_retry
            else "arXiv request failed with transport error."
        )
        log_method = self._logger.warning if will_retry else self._logger.error
        log_method(
            "%s error_type=%s request_url=%s attempt=%s/%s error=%s",
            log_message,
            exc.__class__.__name__,
            request_url,
            attempt + 1,
            self.max_retries + 1,
            str(exc),
        )


def _extract_text(entry: ET.Element, path: str) -> str:
    element = entry.find(path, NAMESPACES)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def _normalize_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def _preview_text(value: str, limit: int = LOG_BODY_PREVIEW_LIMIT) -> str:
    normalized = _normalize_whitespace(value)
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3]}..."


def _extract_arxiv_id(value: str) -> str:
    match = ARXIV_ID_RE.search(value)
    if match is None:
        return ""
    return match.group("identifier")
