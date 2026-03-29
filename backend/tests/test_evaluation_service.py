import time

from app.core.config import Settings
from app.services.evaluation_service import EvaluationService


def test_evaluation_service_collects_stage_timings_and_counts() -> None:
    service = EvaluationService(settings=Settings(enable_metrics_collection=True))
    tracker = service.start_workflow("compare")

    with tracker.stage("retrieval"):
        time.sleep(0.01)

    with tracker.stage("generation"):
        time.sleep(0.01)

    meta = tracker.finalize(
        status="completed",
        retrieved_chunk_count=4,
        citation_count=2,
    )

    assert meta is not None
    assert meta.status == "completed"
    assert meta.retrieval_ms >= 1
    assert meta.generation_ms >= 1
    assert meta.total_ms >= meta.retrieval_ms + meta.generation_ms
    assert meta.retrieved_chunk_count == 4
    assert meta.citation_count == 2


def test_evaluation_service_can_be_disabled() -> None:
    service = EvaluationService(settings=Settings(enable_metrics_collection=False))
    tracker = service.start_workflow("chat")

    with tracker.stage("retrieval"):
        time.sleep(0.005)

    meta = tracker.finalize(
        status="partial",
        retrieved_chunk_count=1,
        citation_count=1,
    )

    assert meta is None
