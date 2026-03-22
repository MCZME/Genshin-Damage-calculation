from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
import multiprocessing
import statistics
from typing import Any
from collections.abc import Callable, Iterable

from core.batch.compiler import BatchProjectCompiler
from core.batch.models import (
    BatchProject,
    BatchRunRequest,
    BatchRunResult,
    BatchRunSummary,
)


def _default_batch_worker(request: BatchRunRequest) -> BatchRunResult:
    from core.data.repository import MySQLDataRepository
    from core.factory.assembler import create_simulator_from_config
    from core.logger import SimulationLogger
    from core.registry import initialize_registry

    initialize_registry()
    repo = MySQLDataRepository()
    simulator = create_simulator_from_config(request.config, repo)
    simulator.ctx.logger = SimulationLogger(
        name=f"BatchRun_{request.node_id}",
        batch_run_id=request.batch_run_id,
        batch_node_id=request.node_id,
    )

    async def _run() -> None:
        await simulator.run()

    asyncio.run(_run())

    duration = getattr(simulator.ctx, "current_frame", 0)
    total_damage = getattr(simulator.ctx, "total_damage", 0.0)
    dps = (total_damage / duration * 60) if duration else 0.0
    return BatchRunResult(
        request_id=request.request_id,
        node_id=request.node_id,
        node_name=request.node_name,
        total_damage=total_damage,
        dps=dps,
        simulation_duration=duration,
        param_snapshot=dict(request.param_snapshot),
    )


class BatchExecutionService:
    """批处理执行服务。"""

    def __init__(
        self,
        max_workers: int | None = None,
        worker_func: Callable[[BatchRunRequest], BatchRunResult] | None = None,
    ) -> None:
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.worker_func = worker_func or _default_batch_worker

    async def run(
        self,
        project: BatchProject | None = None,
        requests: Iterable[BatchRunRequest] | None = None,
        on_progress: Callable[[int, int], Any] | None = None,
    ) -> BatchRunSummary:
        materialized = list(requests) if requests is not None else []
        if project is not None and not materialized:
            materialized = BatchProjectCompiler.compile(project)

        summary = BatchRunSummary(total_runs=len(materialized))
        if not materialized:
            return summary

        loop = asyncio.get_running_loop()

        if self.worker_func is _default_batch_worker:
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=self.max_workers
            ) as executor:
                futures = [
                    loop.run_in_executor(executor, self.worker_func, request)
                    for request in materialized
                ]
                await self._consume_futures(futures, summary, on_progress)
        else:
            futures = [
                loop.run_in_executor(None, self.worker_func, request)
                for request in materialized
            ]
            await self._consume_futures(futures, summary, on_progress)

        self._calculate_stats(summary)
        return summary

    async def _consume_futures(
        self,
        futures: list[asyncio.Future],
        summary: BatchRunSummary,
        on_progress: Callable[[int, int], Any] | None,
    ) -> None:
        completed = 0
        for future in asyncio.as_completed(futures):
            try:
                result = await future
                summary.results.append(result)
                if result.error:
                    summary.failed_runs += 1
                    summary.errors.append(result.error)
                else:
                    summary.completed_runs += 1
            except Exception as exc:
                summary.failed_runs += 1
                summary.errors.append(str(exc))

            completed += 1
            if on_progress:
                if inspect.iscoroutinefunction(on_progress):
                    await on_progress(completed, summary.total_runs)
                else:
                    on_progress(completed, summary.total_runs)

    @staticmethod
    def _calculate_stats(summary: BatchRunSummary) -> None:
        dps_values = [result.dps for result in summary.results if not result.error]
        if not dps_values:
            return

        summary.avg_dps = statistics.mean(dps_values)
        summary.max_dps = max(dps_values)
        summary.min_dps = min(dps_values)
        if len(dps_values) > 1:
            summary.std_dev_dps = statistics.stdev(dps_values)

        sorted_values = sorted(dps_values)
        index = min(int(len(sorted_values) * 0.95), len(sorted_values) - 1)
        summary.p95_dps = sorted_values[index]
