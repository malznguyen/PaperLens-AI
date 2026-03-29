from __future__ import annotations

import logging
from contextlib import contextmanager
from time import perf_counter
from typing import Iterator, Literal

from app.core.config import Settings, get_settings
from app.schemas.chat import WorkflowMeta

WorkflowStatus = Literal["completed", "partial", "failed"]
MetricStage = Literal["retrieval", "reranking", "generation"]

_STAGE_TO_FIELD = {
    "retrieval": "retrieval_ms",
    "reranking": "reranking_ms",
    "generation": "generation_ms",
}


class EvaluationTracker:
    def __init__(
        self,
        *,
        workflow_name: str,
        enabled: bool,
        logger: logging.Logger,
    ) -> None:
        self._workflow_name = workflow_name
        self._enabled = enabled
        self._logger = logger
        self._started_at = perf_counter()
        self._durations = {
            "retrieval_ms": 0,
            "reranking_ms": 0,
            "generation_ms": 0,
        }

    @contextmanager
    def stage(self, name: MetricStage) -> Iterator[None]:
        started_at = perf_counter()
        try:
            yield
        finally:
            field_name = _STAGE_TO_FIELD[name]
            self._durations[field_name] += int((perf_counter() - started_at) * 1000)

    def finalize(
        self,
        *,
        status: WorkflowStatus,
        retrieved_chunk_count: int,
        citation_count: int,
    ) -> WorkflowMeta | None:
        if not self._enabled:
            return None

        meta = WorkflowMeta(
            retrieval_ms=self._durations["retrieval_ms"],
            reranking_ms=self._durations["reranking_ms"],
            generation_ms=self._durations["generation_ms"],
            total_ms=int((perf_counter() - self._started_at) * 1000),
            retrieved_chunk_count=max(retrieved_chunk_count, 0),
            citation_count=max(citation_count, 0),
            status=status,
        )
        self._logger.info(
            "workflow_metrics",
            extra={
                "workflow_name": self._workflow_name,
                "metrics": meta.model_dump(mode="json"),
            },
        )
        return meta


class EvaluationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._logger = logging.getLogger(__name__)

    def start_workflow(self, workflow_name: str) -> EvaluationTracker:
        return EvaluationTracker(
            workflow_name=workflow_name,
            enabled=self._settings.enable_metrics_collection,
            logger=self._logger,
        )
