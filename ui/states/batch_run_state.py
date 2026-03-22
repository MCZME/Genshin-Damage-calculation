from __future__ import annotations

import uuid
from typing import Any, cast

import flet as ft

from core.batch import (
    BRANCH_RUN_BATCH_REQUEST,
    MAIN_BATCH_FINISHED,
    MAIN_BATCH_PROGRESS,
    MAIN_BATCH_REJECTED,
    BatchCompileError,
    BatchProject,
    BatchProjectCompiler,
    BatchRunSummary,
)
from core.logger import get_ui_logger


@ft.observable
class BatchRunState:
    """批处理运行页面状态。"""

    def __init__(self) -> None:
        self.page: Any = None
        self.branch_to_main_queue = None
        self.status_text = "等待执行"
        self.progress = 0.0
        self.is_running = False
        self.active_run_id: str | None = None
        self.error_message = ""
        self.last_summary: BatchRunSummary | None = None

    def notify_update(self) -> None:
        cast(Any, self).notify()  # type: ignore

    def reset(self, status_text: str = "等待执行") -> None:
        self.status_text = status_text
        self.progress = 0.0
        self.is_running = False
        self.active_run_id = None
        self.error_message = ""
        self.last_summary = None
        self.notify_update()

    async def run_batch(self, project: BatchProject) -> BatchRunSummary | None:
        if self.is_running:
            return None

        self.is_running = True
        self.progress = 0.0
        self.status_text = "编译批处理任务中..."
        self.error_message = ""
        self.last_summary = None
        self.notify_update()

        try:
            requests = BatchProjectCompiler.compile(project)
            if not requests:
                self.status_text = "没有可执行的叶子任务"
                self.is_running = False
                self.notify_update()
                return None
            if self.branch_to_main_queue is None:
                raise RuntimeError("IPC 未连接，无法提交到主进程执行。")

            run_id = uuid.uuid4().hex
            self.active_run_id = run_id
            payload = {
                "type": BRANCH_RUN_BATCH_REQUEST,
                "run_id": run_id,
                "project_name": project.name,
                "requests": [request.to_dict() for request in requests],
            }
            self.branch_to_main_queue.put(payload)
            self.status_text = f"已提交主进程执行（{len(requests)} 个任务）"
            self.notify_update()
            return None
        except (BatchCompileError, ValueError) as exc:
            self.error_message = str(exc)
            self.status_text = "批处理执行失败"
            self.is_running = False
            self.active_run_id = None
            self.notify_update()
            raise
        except Exception as exc:
            self.error_message = str(exc)
            self.status_text = "批处理提交失败"
            self.is_running = False
            self.active_run_id = None
            self.notify_update()
            raise

    def handle_main_message(self, message: dict[str, Any]) -> BatchRunSummary | None:
        msg_type = str(message.get("type", ""))
        run_id = str(message.get("run_id", ""))

        if not run_id or run_id != self.active_run_id:
            return None

        if msg_type == MAIN_BATCH_PROGRESS:
            done = int(message.get("done", 0))
            total = int(message.get("total", 0))
            status_text = str(message.get("status_text", f"批处理执行中 {done}/{total}"))
            self.progress = done / total if total else 0.0
            self.status_text = status_text
            self.notify_update()
            return None

        if msg_type == MAIN_BATCH_REJECTED:
            reason = str(message.get("reason", "unknown"))
            detail = str(message.get("message", "主进程拒绝执行请求。"))
            self.error_message = detail
            self.status_text = f"执行被拒绝（{reason}）"
            self.is_running = False
            self.active_run_id = None
            self.notify_update()
            return None

        if msg_type == MAIN_BATCH_FINISHED:
            summary_payload = message.get("summary", {})
            summary = BatchRunSummary.from_dict(summary_payload)
            self.last_summary = summary
            self.progress = 1.0
            first_error = str(message.get("first_error", "") or "")
            if summary.failed_runs > 0:
                self.error_message = first_error or "批处理中存在失败任务，请检查日志。"
            else:
                self.error_message = ""
            self.status_text = (
                f"完成 {summary.completed_runs}/{summary.total_runs}，"
                f"失败 {summary.failed_runs}，平均 DPS {int(summary.avg_dps)}"
            )
            self.is_running = False
            self.active_run_id = None
            self.notify_update()
            return summary

        return None

    def handle_main_error(self, run_id: str | None, error_text: str) -> None:
        if not run_id or run_id != self.active_run_id:
            return
        get_ui_logger().log_error(f"Batch editor main-side error: {error_text}")
        self.error_message = error_text
        self.status_text = "主进程执行失败"
        self.is_running = False
        self.active_run_id = None
        self.notify_update()
