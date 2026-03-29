from __future__ import annotations

from collections import defaultdict

from app.core.config import Settings, get_settings
from app.repositories.chroma_repository import ChromaRepository, ChromaRepositoryError
from app.schemas.chat import RetrievedChunk
from app.schemas.compare import (
    ComparisonRow,
    CompareRequest,
    CompareResponse,
    GeneratedComparisonPayload,
    MISSING_EVIDENCE_TEXT,
)
from app.services.citation_service import CitationService
from app.services.evaluation_service import EvaluationService
from app.services.generation_service import GenerationService, GenerationServiceError
from app.services.reranking_service import RerankingService, RerankingServiceError
from app.services.retrieval_service import (
    RetrievalNoIndexedPapersError,
    RetrievalNoRelevantChunksError,
    RetrievalService,
    RetrievalServiceError,
)
from app.utils.prompt_utils import render_chunk_for_prompt


class CompareWorkflowNotReadyError(RuntimeError):
    """Raised when one or more selected papers are not indexed."""


class CompareWorkflowEvidenceError(RuntimeError):
    """Raised when grounded comparison evidence cannot be assembled."""


class CompareWorkflowError(RuntimeError):
    """Raised when comparison infrastructure fails."""


class CompareWorkflow:
    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
        reranking_service: RerankingService | None = None,
        generation_service: GenerationService | None = None,
        citation_service: CitationService | None = None,
        evaluation_service: EvaluationService | None = None,
        chroma_repository: ChromaRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._retrieval_service = retrieval_service or RetrievalService()
        self._reranking_service = reranking_service or RerankingService(settings=self._settings)
        self._generation_service = generation_service or GenerationService(settings=self._settings)
        self._citation_service = citation_service or CitationService()
        self._evaluation_service = evaluation_service or EvaluationService(settings=self._settings)
        self._chroma_repository = chroma_repository or ChromaRepository(settings=self._settings)

    async def compare_papers(self, payload: CompareRequest) -> CompareResponse:
        tracker = self._evaluation_service.start_workflow("compare")
        paper_titles = self._ensure_indexed_papers(payload.paper_ids)
        retrieval_query = self._build_retrieval_query(payload.resolved_question)
        retrieval_limit = self._comparison_retrieval_limit()

        retrieved_by_paper: dict[str, list[RetrievedChunk]] = {}
        with tracker.stage("retrieval"):
            for paper_id in payload.paper_ids:
                try:
                    retrieved_by_paper[paper_id] = await self._retrieval_service.retrieve_chunks(
                        retrieval_query,
                        paper_ids=[paper_id],
                        top_k=retrieval_limit,
                    )
                except RetrievalNoRelevantChunksError as exc:
                    raise CompareWorkflowEvidenceError(
                        f"Paper {paper_id} does not have enough usable evidence for this comparison request."
                    ) from exc
                except RetrievalNoIndexedPapersError as exc:
                    raise CompareWorkflowNotReadyError(str(exc)) from exc
                except RetrievalServiceError as exc:
                    raise CompareWorkflowError(str(exc)) from exc

                if retrieved_by_paper[paper_id]:
                    paper_titles[paper_id] = retrieved_by_paper[paper_id][0].paper_title

        ranked_by_paper = retrieved_by_paper
        if self._reranking_service.enabled:
            reranked_results: dict[str, list[RetrievedChunk]] = {}
            with tracker.stage("reranking"):
                for paper_id, chunks in retrieved_by_paper.items():
                    try:
                        reranked_results[paper_id] = await self._reranking_service.rerank_chunks(
                            payload.resolved_question,
                            chunks,
                            top_k=self._settings.compare_top_k_per_paper,
                        )
                    except RerankingServiceError:
                        reranked_results[paper_id] = chunks[: self._settings.compare_top_k_per_paper]
            ranked_by_paper = reranked_results

        combined_chunks: list[RetrievedChunk] = []
        for paper_id in payload.paper_ids:
            combined_chunks.extend(ranked_by_paper[paper_id][: self._settings.compare_top_k_per_paper])

        prepared_chunks = self._citation_service.prepare_context_chunks(
            combined_chunks,
            top_k=len(combined_chunks),
        )
        context_chunks = self._select_balanced_context_chunks(prepared_chunks, payload.paper_ids)
        candidate_citations = self._citation_service.build_citations(context_chunks)

        try:
            with tracker.stage("generation"):
                generated_payload = await self._generation_service.generate_structured_payload(
                    self._build_messages(
                        question=payload.resolved_question,
                        paper_ids=payload.paper_ids,
                        chunks=context_chunks,
                    ),
                    response_model=GeneratedComparisonPayload,
                    temperature=self._settings.compare_generation_temperature,
                    max_tokens=900,
                )
        except GenerationServiceError:
            meta = tracker.finalize(
                status="partial",
                retrieved_chunk_count=len(context_chunks),
                citation_count=len(candidate_citations),
            )
            return CompareResponse(
                status="partial",
                summary=None,
                comparison_table=self._build_fallback_rows(payload.paper_ids, paper_titles),
                citations=candidate_citations,
                retrieved_chunks=context_chunks,
                meta=meta,
                message="Evidence retrieved, but comparison generation failed.",
            )

        resolved_citations = self._citation_service.resolve_citations(
            generated_payload.citations,
            context_chunks,
        )
        comparison_rows = self._normalize_rows(
            generated_payload.comparison_table,
            payload.paper_ids,
            paper_titles,
        )
        message = "Comparison generated successfully."
        if generated_payload.insufficient_evidence:
            message = "Comparison generated with limited evidence from the retrieved chunks."

        meta = tracker.finalize(
            status="completed",
            retrieved_chunk_count=len(context_chunks),
            citation_count=len(resolved_citations),
        )
        return CompareResponse(
            status="completed",
            summary=generated_payload.summary,
            comparison_table=comparison_rows,
            citations=resolved_citations,
            retrieved_chunks=context_chunks,
            meta=meta,
            message=message,
        )

    def _ensure_indexed_papers(self, paper_ids: list[str]) -> dict[str, str]:
        missing_ids: list[str] = []
        paper_titles: dict[str, str] = {}

        for paper_id in paper_ids:
            try:
                chunk_count = self._chroma_repository.count_chunks_for_paper(paper_id)
            except ChromaRepositoryError as exc:
                raise CompareWorkflowError("Failed to verify indexed paper availability for comparison.") from exc

            if chunk_count == 0:
                missing_ids.append(paper_id)
            else:
                paper_titles[paper_id] = paper_id

        if missing_ids:
            joined_ids = ", ".join(missing_ids)
            raise CompareWorkflowNotReadyError(
                f"These paper IDs are not indexed yet: {joined_ids}."
            )

        return paper_titles

    def _comparison_retrieval_limit(self) -> int:
        base_limit = self._settings.compare_top_k_per_paper
        if self._reranking_service.enabled:
            return min(self._settings.retrieval_top_k_max, max(base_limit, base_limit * 2))
        return base_limit

    @staticmethod
    def _build_retrieval_query(question: str) -> str:
        return (
            f"{question}\n\nFocus on objective, methodology, dataset usage, strengths, "
            "limitations, and key contribution."
        )

    def _select_balanced_context_chunks(
        self,
        chunks: list[RetrievedChunk],
        paper_ids: list[str],
    ) -> list[RetrievedChunk]:
        grouped_chunks: dict[str, list[RetrievedChunk]] = defaultdict(list)
        for chunk in chunks:
            grouped_chunks[chunk.paper_id].append(chunk)

        selected_chunks: list[RetrievedChunk] = []
        selected_counts = {paper_id: 0 for paper_id in paper_ids}
        current_length = 0
        chunk_offset = 0

        while True:
            added_any = False
            for paper_id in paper_ids:
                paper_chunks = grouped_chunks.get(paper_id, [])
                if chunk_offset >= len(paper_chunks):
                    continue

                chunk = paper_chunks[chunk_offset]
                chunk_block = render_chunk_for_prompt(
                    chunk,
                    max_chunk_chars=self._settings.generation_chunk_char_limit,
                )
                would_exceed_limit = (
                    bool(selected_chunks)
                    and current_length + len(chunk_block) > self._settings.generation_context_char_limit
                )
                must_include = selected_counts[paper_id] == 0
                if would_exceed_limit and not must_include:
                    continue

                selected_chunks.append(chunk)
                selected_counts[paper_id] += 1
                current_length += len(chunk_block)
                added_any = True

            if not added_any:
                break
            chunk_offset += 1

        return selected_chunks or chunks[:1]

    def _build_messages(
        self,
        *,
        question: str,
        paper_ids: list[str],
        chunks: list[RetrievedChunk],
    ) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": (
                    "You are PaperLens AI, a grounded academic comparison assistant. "
                    "Use only the retrieved evidence provided. "
                    "Do not use outside knowledge. "
                    "Do not invent datasets, limitations, strengths, or contributions. "
                    f"If a field is not supported, use the exact string '{MISSING_EVIDENCE_TEXT}'. "
                    "Return strict JSON only with this shape: "
                    '{"summary":"...","comparison_table":[{"paper_id":"...","paper_title":"...",'
                    '"objective":"...","methodology":"...","dataset":"...","strengths":"...",'
                    '"limitations":"...","key_contribution":"..."}],"citations":["S1"],'
                    '"insufficient_evidence":false}. '
                    "Include exactly one comparison_table row for each requested paper ID in the same order. "
                    "Only use citation labels that appear in the retrieved evidence. "
                    "Do not include markdown fences or extra commentary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Comparison question:\n{question}\n\n"
                    f"Selected paper IDs in required order:\n{', '.join(paper_ids)}\n\n"
                    "Retrieved evidence grouped by paper:\n"
                    f"{self._build_grouped_context_block(paper_ids, chunks)}\n\n"
                    "Write a grounded comparison summary and structured table."
                ),
            },
        ]

    def _build_grouped_context_block(
        self,
        paper_ids: list[str],
        chunks: list[RetrievedChunk],
    ) -> str:
        grouped_chunks: dict[str, list[RetrievedChunk]] = defaultdict(list)
        for chunk in chunks:
            grouped_chunks[chunk.paper_id].append(chunk)

        sections: list[str] = []
        for paper_id in paper_ids:
            paper_chunks = grouped_chunks.get(paper_id, [])
            if not paper_chunks:
                continue

            section_lines = [
                f"paper_id: {paper_id}",
                f"paper_title: {paper_chunks[0].paper_title}",
            ]
            section_lines.extend(
                render_chunk_for_prompt(
                    chunk,
                    max_chunk_chars=self._settings.generation_chunk_char_limit,
                )
                for chunk in paper_chunks
            )
            sections.append("\n\n".join(section_lines))

        return "\n\n---\n\n".join(sections)

    @staticmethod
    def _build_fallback_rows(
        paper_ids: list[str],
        paper_titles: dict[str, str],
    ) -> list[ComparisonRow]:
        return [
            ComparisonRow(
                paper_id=paper_id,
                paper_title=paper_titles.get(paper_id, paper_id),
                objective=MISSING_EVIDENCE_TEXT,
                methodology=MISSING_EVIDENCE_TEXT,
                dataset=MISSING_EVIDENCE_TEXT,
                strengths=MISSING_EVIDENCE_TEXT,
                limitations=MISSING_EVIDENCE_TEXT,
                key_contribution=MISSING_EVIDENCE_TEXT,
            )
            for paper_id in paper_ids
        ]

    @staticmethod
    def _normalize_rows(
        rows: list[ComparisonRow],
        paper_ids: list[str],
        paper_titles: dict[str, str],
    ) -> list[ComparisonRow]:
        row_by_id: dict[str, ComparisonRow] = {}
        for row in rows:
            if row.paper_id in paper_ids and row.paper_id not in row_by_id:
                row_by_id[row.paper_id] = row

        normalized_rows: list[ComparisonRow] = []
        for paper_id in paper_ids:
            row = row_by_id.get(paper_id)
            if row is None:
                normalized_rows.append(
                    ComparisonRow(
                        paper_id=paper_id,
                        paper_title=paper_titles.get(paper_id, paper_id),
                    )
                )
                continue

            normalized_rows.append(
                row.model_copy(
                    update={
                        "paper_id": paper_id,
                        "paper_title": paper_titles.get(paper_id, row.paper_title),
                    }
                )
            )

        return normalized_rows
