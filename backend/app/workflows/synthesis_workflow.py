from __future__ import annotations

from app.core.config import Settings, get_settings
from app.repositories.chroma_repository import ChromaRepository, ChromaRepositoryError
from app.schemas.chat import RetrievedChunk
from app.schemas.synthesis import (
    GeneratedSynthesisPayload,
    TopicSynthesisRequest,
    TopicSynthesisResponse,
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
from app.utils.prompt_utils import build_context_block, select_context_chunks


class SynthesisWorkflowNotReadyError(RuntimeError):
    """Raised when the requested synthesis corpus is not indexed yet."""


class SynthesisWorkflowEvidenceError(RuntimeError):
    """Raised when synthesis cannot be grounded with usable evidence."""


class SynthesisWorkflowError(RuntimeError):
    """Raised when synthesis infrastructure fails."""


class SynthesisWorkflow:
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

    async def summarize_topic(self, payload: TopicSynthesisRequest) -> TopicSynthesisResponse:
        tracker = self._evaluation_service.start_workflow("synthesis")
        self._ensure_indexed_papers(payload.paper_ids)

        retrieval_limit = self._synthesis_retrieval_limit()
        with tracker.stage("retrieval"):
            try:
                retrieved_chunks = await self._retrieval_service.retrieve_chunks(
                    payload.retrieval_query,
                    paper_ids=payload.paper_ids or None,
                    top_k=retrieval_limit,
                )
            except RetrievalNoIndexedPapersError as exc:
                raise SynthesisWorkflowNotReadyError(str(exc)) from exc
            except RetrievalNoRelevantChunksError as exc:
                raise SynthesisWorkflowEvidenceError(str(exc)) from exc
            except RetrievalServiceError as exc:
                raise SynthesisWorkflowError(str(exc)) from exc

        if self._reranking_service.enabled:
            with tracker.stage("reranking"):
                try:
                    ranked_chunks = await self._reranking_service.rerank_chunks(
                        payload.retrieval_query,
                        retrieved_chunks,
                        top_k=self._settings.synthesis_top_k,
                    )
                except RerankingServiceError:
                    ranked_chunks = retrieved_chunks[: self._settings.synthesis_top_k]
        else:
            ranked_chunks = retrieved_chunks[: self._settings.synthesis_top_k]

        context_chunks = self._citation_service.prepare_context_chunks(
            ranked_chunks,
            top_k=self._settings.synthesis_top_k,
        )
        context_chunks = select_context_chunks(
            context_chunks,
            max_chunk_chars=self._settings.generation_chunk_char_limit,
            max_context_chars=self._settings.generation_context_char_limit,
        )
        candidate_citations = self._citation_service.build_citations(context_chunks)

        try:
            with tracker.stage("generation"):
                generated_payload = await self._generation_service.generate_structured_payload(
                    self._build_messages(payload, context_chunks),
                    response_model=GeneratedSynthesisPayload,
                    temperature=self._settings.synthesis_generation_temperature,
                    max_tokens=900,
                )
        except GenerationServiceError:
            meta = tracker.finalize(
                status="partial",
                retrieved_chunk_count=len(context_chunks),
                citation_count=len(candidate_citations),
            )
            return TopicSynthesisResponse(
                status="partial",
                topic=payload.display_topic,
                overview=None,
                citations=candidate_citations,
                retrieved_chunks=context_chunks,
                meta=meta,
                message="Evidence retrieved, but topic synthesis generation failed.",
            )

        resolved_citations = self._citation_service.resolve_citations(
            generated_payload.citations,
            context_chunks,
        )
        message = "Topic synthesis generated successfully."
        if generated_payload.insufficient_evidence:
            message = "Topic synthesis generated with limited evidence from the retrieved chunks."

        meta = tracker.finalize(
            status="completed",
            retrieved_chunk_count=len(context_chunks),
            citation_count=len(resolved_citations),
        )
        return TopicSynthesisResponse(
            status="completed",
            topic=generated_payload.topic or payload.display_topic,
            overview=generated_payload.overview,
            themes=generated_payload.themes,
            trends=generated_payload.trends,
            open_challenges=generated_payload.open_challenges,
            research_gaps=generated_payload.research_gaps,
            future_directions=generated_payload.future_directions,
            citations=resolved_citations,
            retrieved_chunks=context_chunks,
            meta=meta,
            message=message,
        )

    def _ensure_indexed_papers(self, paper_ids: list[str]) -> None:
        if not paper_ids:
            return

        missing_ids: list[str] = []
        for paper_id in paper_ids:
            try:
                chunk_count = self._chroma_repository.count_chunks_for_paper(paper_id)
            except ChromaRepositoryError as exc:
                raise SynthesisWorkflowError("Failed to verify indexed paper availability for synthesis.") from exc

            if chunk_count == 0:
                missing_ids.append(paper_id)

        if missing_ids:
            joined_ids = ", ".join(missing_ids)
            raise SynthesisWorkflowNotReadyError(
                f"These paper IDs are not indexed yet: {joined_ids}."
            )

    def _synthesis_retrieval_limit(self) -> int:
        if self._reranking_service.enabled:
            return min(
                self._settings.retrieval_top_k_max,
                max(self._settings.synthesis_top_k, self._settings.synthesis_top_k * 2),
            )
        return self._settings.synthesis_top_k

    def _build_messages(
        self,
        payload: TopicSynthesisRequest,
        context_chunks: list[RetrievedChunk],
    ) -> list[dict[str, str]]:
        context_block = build_context_block(
            context_chunks,
            max_chunk_chars=self._settings.generation_chunk_char_limit,
        )
        paper_scope = ", ".join(payload.paper_ids) if payload.paper_ids else "all indexed papers"
        return [
            {
                "role": "system",
                "content": (
                    "You are PaperLens AI, a grounded literature synthesis assistant. "
                    "Use only the retrieved evidence provided. "
                    "Do not use outside knowledge. "
                    "Do not invent consensus, open challenges, research gaps, or future directions. "
                    "If the evidence is uncertain or mixed, say so explicitly in the overview. "
                    "Return strict JSON only with this shape: "
                    '{"topic":"...","overview":"...","themes":["..."],"trends":["..."],'
                    '"open_challenges":["..."],"research_gaps":["..."],"future_directions":["..."],'
                    '"citations":["S1"],"insufficient_evidence":false}. '
                    "Use empty arrays when the evidence does not support a category. "
                    "Only use citation labels that appear in the retrieved evidence. "
                    "Do not include markdown fences or extra commentary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Requested topic: {payload.display_topic}\n"
                    f"Paper scope: {paper_scope}\n\n"
                    "Retrieved evidence:\n"
                    f"{context_block}\n\n"
                    "Generate a grounded topic synthesis that is useful for a literature review workflow."
                ),
            },
        ]
