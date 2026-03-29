from __future__ import annotations

from app.schemas.chat import ChatCitation, RetrievedChunk
from app.utils.chunk_utils import normalize_whitespace


class CitationService:
    def prepare_context_chunks(
        self,
        chunks: list[RetrievedChunk],
        *,
        top_k: int,
    ) -> list[RetrievedChunk]:
        deduplicated_chunks: list[RetrievedChunk] = []
        seen_texts: set[tuple[str, str]] = set()

        for chunk in chunks:
            normalized_text = normalize_whitespace(chunk.text).lower()
            dedupe_key = (chunk.paper_id, normalized_text)
            if not normalized_text or dedupe_key in seen_texts:
                continue

            seen_texts.add(dedupe_key)
            deduplicated_chunks.append(chunk)

            if len(deduplicated_chunks) >= top_k:
                break

        labeled_chunks: list[RetrievedChunk] = []
        for index, chunk in enumerate(deduplicated_chunks, start=1):
            labeled_chunks.append(chunk.model_copy(update={"label": f"S{index}"}))

        return labeled_chunks

    def build_citations(self, chunks: list[RetrievedChunk]) -> list[ChatCitation]:
        return [self._chunk_to_citation(chunk) for chunk in chunks]

    def resolve_citations(
        self,
        citation_labels: list[str],
        chunks: list[RetrievedChunk],
    ) -> list[ChatCitation]:
        chunk_by_label = {
            chunk.label: chunk
            for chunk in chunks
            if chunk.label is not None
        }

        resolved_citations: list[ChatCitation] = []
        seen_labels: set[str] = set()
        for label in citation_labels:
            if label in seen_labels:
                continue

            chunk = chunk_by_label.get(label)
            if chunk is None:
                continue

            seen_labels.add(label)
            resolved_citations.append(self._chunk_to_citation(chunk))

        if resolved_citations:
            return resolved_citations

        return self.build_citations(chunks)

    def compose_answer(
        self,
        answer_text: str,
        citations: list[ChatCitation],
    ) -> str:
        if not citations:
            return answer_text.strip()

        source_lines = [
            f"[{citation.label}] {citation.paper_title} ({citation.paper_id}), p. {citation.page_number}"
            for citation in citations
        ]
        return answer_text.strip() + "\n\nSources:\n" + "\n".join(source_lines)

    @staticmethod
    def _chunk_to_citation(chunk: RetrievedChunk) -> ChatCitation:
        return ChatCitation(
            label=chunk.label or chunk.chunk_id,
            paper_id=chunk.paper_id,
            paper_title=chunk.paper_title,
            page_number=chunk.page_number,
            chunk_id=chunk.chunk_id,
            source_url=chunk.source_url,
        )
