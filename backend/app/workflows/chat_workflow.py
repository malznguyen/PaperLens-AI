from __future__ import annotations

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.citation_service import CitationService
from app.services.generation_service import GenerationService, GenerationServiceError
from app.services.reranking_service import RerankingService, RerankingServiceError
from app.services.retrieval_service import RetrievalService
from app.utils.prompt_utils import select_context_chunks


class ChatWorkflow:
    def __init__(
        self,
        retrieval_service: RetrievalService | None = None,
        reranking_service: RerankingService | None = None,
        generation_service: GenerationService | None = None,
        citation_service: CitationService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._retrieval_service = retrieval_service or RetrievalService()
        self._reranking_service = reranking_service or RerankingService(settings=self._settings)
        self._generation_service = generation_service or GenerationService(settings=self._settings)
        self._citation_service = citation_service or CitationService()

    async def answer_question(self, payload: ChatRequest) -> ChatResponse:
        requested_top_k = payload.top_k or self._settings.retrieval_top_k_default
        retrieval_limit = requested_top_k
        if self._reranking_service.enabled:
            retrieval_limit = min(
                self._settings.retrieval_top_k_max,
                max(requested_top_k, requested_top_k * 2),
            )

        retrieved_chunks = await self._retrieval_service.retrieve_chunks(
            payload.question,
            paper_ids=payload.paper_ids,
            top_k=retrieval_limit,
        )

        if self._reranking_service.enabled:
            try:
                ranked_chunks = await self._reranking_service.rerank_chunks(
                    payload.question,
                    retrieved_chunks,
                    top_k=requested_top_k,
                )
            except RerankingServiceError:
                ranked_chunks = retrieved_chunks[:requested_top_k]
        else:
            ranked_chunks = retrieved_chunks[:requested_top_k]

        context_chunks = self._citation_service.prepare_context_chunks(
            ranked_chunks,
            top_k=requested_top_k,
        )
        context_chunks = select_context_chunks(
            context_chunks,
            max_chunk_chars=self._settings.generation_chunk_char_limit,
            max_context_chars=self._settings.generation_context_char_limit,
        )
        citation_candidates = self._citation_service.build_citations(context_chunks)

        try:
            generated_answer = await self._generation_service.generate_answer(
                payload.question,
                context_chunks,
            )
        except GenerationServiceError:
            return ChatResponse(
                status="partial",
                question=payload.question,
                answer=None,
                citations=citation_candidates,
                retrieved_chunks=context_chunks,
                message="Evidence retrieved, but answer generation failed.",
            )

        resolved_citations = self._citation_service.resolve_citations(
            generated_answer.citation_labels,
            context_chunks,
        )
        answer = self._citation_service.compose_answer(
            generated_answer.answer,
            resolved_citations,
        )
        message = "Answer generated successfully."
        if generated_answer.insufficient_evidence:
            message = "Answer generated with limited evidence from the retrieved chunks."

        return ChatResponse(
            status="completed",
            question=payload.question,
            answer=answer,
            citations=resolved_citations,
            retrieved_chunks=context_chunks,
            message=message,
        )
