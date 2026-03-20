import pytest

from core.batch.execution import BatchExecutionService
from core.batch.models import BatchRunRequest, BatchRunResult


@pytest.mark.asyncio
async def test_execution_service_collects_success_stats_and_progress():
    calls = []

    def worker(request: BatchRunRequest) -> BatchRunResult:
        return BatchRunResult(
            request_id=request.request_id,
            node_id=request.node_id,
            node_name=request.node_name,
            total_damage=1000,
            dps=500 + len(calls) * 100,
            simulation_duration=120,
            param_snapshot=request.param_snapshot,
        )

    def on_progress(done: int, total: int) -> None:
        calls.append((done, total))

    service = BatchExecutionService(worker_func=worker)
    requests = [
        BatchRunRequest("a", "a", "A", {"x": 1}),
        BatchRunRequest("b", "b", "B", {"x": 2}),
    ]

    summary = await service.run(requests=requests, on_progress=on_progress)

    assert summary.total_runs == 2
    assert summary.completed_runs == 2
    assert summary.failed_runs == 0
    assert summary.avg_dps >= 500
    assert calls[-1] == (2, 2)


@pytest.mark.asyncio
async def test_execution_service_records_worker_errors():
    def worker(request: BatchRunRequest) -> BatchRunResult:
        if request.node_id == "bad":
            raise RuntimeError("boom")
        return BatchRunResult(
            request_id=request.request_id,
            node_id=request.node_id,
            node_name=request.node_name,
            total_damage=1000,
            dps=500,
            simulation_duration=120,
            param_snapshot=request.param_snapshot,
        )

    service = BatchExecutionService(worker_func=worker)
    summary = await service.run(
        requests=[
            BatchRunRequest("good", "good", "Good", {"x": 1}),
            BatchRunRequest("bad", "bad", "Bad", {"x": 2}),
        ]
    )

    assert summary.total_runs == 2
    assert summary.completed_runs == 1
    assert summary.failed_runs == 1
    assert summary.errors == ["boom"]
