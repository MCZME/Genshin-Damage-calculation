from __future__ import annotations

import uuid
from typing import Any, cast

import flet as ft

from core.batch import (
    BRANCH_RUN_BATCH_REQUEST,
    MAIN_BATCH_FINISHED,
    MAIN_BATCH_PROGRESS,
    MAIN_BATCH_REJECTED,
    MAIN_BATCH_TASK_RESULT,
    BatchCompileError,
    BatchProject,
    BatchProjectCompiler,
    BatchRunRequest,
    BatchRunResult,
    BatchRunSummary,
    TaskRunState,
)
from core.logger import get_ui_logger
from ui.view_models.universe.run_task_vm import RunTaskViewModel


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
        # 任务列表管理
        self.tasks: dict[str, RunTaskViewModel] = {}
        self.task_order: list[str] = []
        self.current_running_id: str | None = None
        # 控制台
        self.console_visible = False
        self.console_logs: list[str] = []

    def notify_update(self) -> None:
        cast(Any, self).notify()  # type: ignore

    def reset(self, status_text: str = "等待执行") -> None:
        self.status_text = status_text
        self.progress = 0.0
        self.is_running = False
        self.active_run_id = None
        self.error_message = ""
        self.last_summary = None
        self.tasks = {}
        self.task_order = []
        self.current_running_id = None
        self.console_visible = False
        self.console_logs = []
        self.notify_update()

    # --- 任务列表管理 ---

    def initialize_tasks(self, requests: list[BatchRunRequest]) -> None:
        """初始化任务列表。"""
        self.tasks = {}
        self.task_order = []
        for req in requests:
            vm = RunTaskViewModel(
                request_id=req.request_id,
                node_id=req.node_id,
                node_name=req.node_name,
                state=TaskRunState.PENDING,
                param_snapshot=req.param_snapshot,
            )
            self.tasks[req.request_id] = vm
            self.task_order.append(req.request_id)
        self.notify_update()

    def set_task_running(self, request_id: str) -> None:
        """设置任务为运行中状态。

        注意：只有当任务处于 PENDING 状态时才更新，避免覆盖已完成的任务状态。
        """
        if request_id in self.tasks:
            vm = self.tasks[request_id]
            # 只有 PENDING 状态才更新为 RUNNING
            if vm.state == TaskRunState.PENDING:
                vm.set_state(TaskRunState.RUNNING)
                self.current_running_id = request_id

    def update_task_result(self, result: BatchRunResult) -> None:
        """更新任务结果。"""
        request_id = result.request_id
        if request_id not in self.tasks:
            return
        vm = self.tasks[request_id]
        if result.error:
            vm.set_error(result.error)
            self.append_log(f"[ERROR] {result.node_name}: {result.error}")
        else:
            vm.set_result(
                total_damage=result.total_damage,
                dps=result.dps,
                simulation_duration=result.simulation_duration,
                param_snapshot=result.param_snapshot,
            )
        if self.current_running_id == request_id:
            self.current_running_id = None

    # --- 控制台管理 ---

    def toggle_console(self) -> None:
        """切换控制台显示。"""
        self.console_visible = not self.console_visible
        self.notify_update()

    def show_console(self) -> None:
        """显示控制台。"""
        self.console_visible = True
        self.notify_update()

    def hide_console(self) -> None:
        """隐藏控制台。"""
        self.console_visible = False
        self.notify_update()

    def append_log(self, message: str) -> None:
        """追加日志。"""
        self.console_logs.append(message)
        self.notify_update()

    # --- 统计属性 ---

    @property
    def total_count(self) -> int:
        """总任务数。"""
        return len(self.task_order)

    @property
    def success_count(self) -> int:
        """成功任务数。"""
        return sum(
            1 for rid in self.task_order
            if self.tasks.get(rid, RunTaskViewModel("", "", "")).state == TaskRunState.SUCCESS
        )

    @property
    def error_count(self) -> int:
        """失败任务数。"""
        return sum(
            1 for rid in self.task_order
            if self.tasks.get(rid, RunTaskViewModel("", "", "")).state == TaskRunState.ERROR
        )

    @property
    def pending_count(self) -> int:
        """等待中任务数。"""
        return sum(
            1 for rid in self.task_order
            if self.tasks.get(rid, RunTaskViewModel("", "", "")).state == TaskRunState.PENDING
        )

    @property
    def running_count(self) -> int:
        """运行中任务数。"""
        return sum(
            1 for rid in self.task_order
            if self.tasks.get(rid, RunTaskViewModel("", "", "")).state == TaskRunState.RUNNING
        )

    async def run_batch(self, project: BatchProject) -> BatchRunSummary | None:
        if self.is_running:
            return None

        self.is_running = True
        self.progress = 0.0
        self.status_text = "编译批处理任务中..."
        self.error_message = ""
        self.last_summary = None
        self.console_logs = []
        self.console_visible = False
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

            # 初始化任务列表
            self.initialize_tasks(requests)
            self.append_log(f"[INFO] 编译完成，共 {len(requests)} 个任务")

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
            self.append_log("[INFO] 已提交到主进程执行")
            self.notify_update()
            return None
        except (BatchCompileError, ValueError) as exc:
            self.error_message = str(exc)
            self.status_text = "批处理执行失败"
            self.is_running = False
            self.active_run_id = None
            self.append_log(f"[ERROR] 编译失败: {exc}")
            self.notify_update()
            raise
        except Exception as exc:
            self.error_message = str(exc)
            self.status_text = "批处理提交失败"
            self.is_running = False
            self.active_run_id = None
            self.append_log(f"[ERROR] 提交失败: {exc}")
            self.notify_update()
            raise

    def handle_main_message(self, message: dict[str, Any]) -> BatchRunSummary | None:
        msg_type = str(message.get("type", ""))
        run_id = str(message.get("run_id", ""))

        if not run_id or run_id != self.active_run_id:
            return None

        if msg_type == MAIN_BATCH_TASK_RESULT:
            result_payload = message.get("result", {})
            result = BatchRunResult.from_dict(result_payload)
            self.update_task_result(result)
            return None

        if msg_type == MAIN_BATCH_PROGRESS:
            done = int(message.get("done", 0))
            total = int(message.get("total", 0))
            running_request_id = message.get("running_request_id")
            status_text = str(message.get("status_text", f"批处理执行中 {done}/{total}"))
            self.progress = done / total if total else 0.0
            self.status_text = status_text
            # 设置当前运行的任务
            if running_request_id:
                self.set_task_running(str(running_request_id))
            self.notify_update()
            return None

        if msg_type == MAIN_BATCH_REJECTED:
            reason = str(message.get("reason", "unknown"))
            detail = str(message.get("message", "主进程拒绝执行请求。"))
            self.error_message = detail
            self.status_text = f"执行被拒绝（{reason}）"
            self.is_running = False
            self.active_run_id = None
            self.append_log(f"[ERROR] 执行被拒绝: {detail}")
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
                self.show_console()  # 错误时自动显示控制台
            else:
                self.error_message = ""
            self.status_text = (
                f"完成 {summary.completed_runs}/{summary.total_runs}，"
                f"失败 {summary.failed_runs}，平均 DPS {int(summary.avg_dps)}"
            )
            self.is_running = False
            self.active_run_id = None
            self.append_log(f"[INFO] 执行完成，平均 DPS {int(summary.avg_dps)}")
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
