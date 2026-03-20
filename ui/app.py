from __future__ import annotations

import json
import multiprocessing
import asyncio

import flet as ft

from core.batch import (
    BRANCH_RUN_BATCH_REQUEST,
    BatchExecutionService,
    BatchRunRequest,
    MAIN_BATCH_FINISHED,
    MAIN_BATCH_PROGRESS,
    MAIN_BATCH_REJECTED,
)
from core.logger import get_ui_logger
from ui.layout import AppLayout
from ui.services.persistence_manager import PersistenceManager
from ui.states.app_state import AppState
from ui.universe_launcher import start_universe_process


def _sanitize_for_ipc(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _sanitize_for_ipc(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_for_ipc(item) for item in value]
    if hasattr(value, "to_simulator_format"):
        return _sanitize_for_ipc(value.to_simulator_format())
    if hasattr(value, "raw_data"):
        return _sanitize_for_ipc(value.raw_data)
    if hasattr(value, "_data"):
        return _sanitize_for_ipc(value._data)
    return str(value)


def main(page: ft.Page, main_to_branch, branch_to_main):
    # 1. 初始化应用状态
    state = AppState()
    state.register_page(page)
    state.main_to_branch = main_to_branch
    state.branch_to_main = branch_to_main

    # 1.1 初始化持久化服务
    persistence = PersistenceManager(page, state)
    setattr(page, "persistence", persistence)
    get_ui_logger().log_info("Genshin Workbench main window initialized.")

    batch_process: multiprocessing.Process | None = None
    batch_executor = BatchExecutionService()
    main_batch_running = False

    def send_to_branch(payload: dict) -> None:
        main_to_branch.put(payload)

    async def open_batch_editor():
        nonlocal batch_process
        if batch_process is None or not batch_process.is_alive():
            batch_process = multiprocessing.Process(
                target=start_universe_process,
                args=(main_to_branch, branch_to_main),
                daemon=True,
            )
            batch_process.start()
            get_ui_logger().log_info("Batch editor process started.")

        sanitized_config = json.loads(
            json.dumps(_sanitize_for_ipc(state.export_config()), ensure_ascii=False)
        )
        main_to_branch.put(
            {
                "type": "INIT_BATCH_EDITOR",
                "config": sanitized_config,
                "project_name": "工作台批处理项目",
            }
        )
        get_ui_logger().log_info("Workbench config sent to batch editor.")

    async def listen_branch_requests():
        nonlocal main_batch_running
        while True:
            if branch_to_main.empty():
                await asyncio.sleep(0.1)
                continue

            message: dict = branch_to_main.get()
            msg_type = str(message.get("type", ""))
            if msg_type != BRANCH_RUN_BATCH_REQUEST:
                await asyncio.sleep(0.05)
                continue

            run_id = str(message.get("run_id", ""))
            if not run_id:
                await asyncio.sleep(0.05)
                continue

            if main_batch_running:
                send_to_branch(
                    {
                        "type": MAIN_BATCH_REJECTED,
                        "run_id": run_id,
                        "reason": "busy",
                        "message": "主进程已有批处理任务在执行，请稍后重试。",
                    }
                )
                await asyncio.sleep(0.05)
                continue

            try:
                requests = [
                    BatchRunRequest.from_dict(item)
                    for item in message.get("requests", [])
                ]
            except Exception as exc:
                send_to_branch(
                    {
                        "type": MAIN_BATCH_REJECTED,
                        "run_id": run_id,
                        "reason": "invalid_payload",
                        "message": f"批处理请求解析失败: {exc}",
                    }
                )
                await asyncio.sleep(0.05)
                continue

            if not requests:
                send_to_branch(
                    {
                        "type": MAIN_BATCH_REJECTED,
                        "run_id": run_id,
                        "reason": "empty_requests",
                        "message": "请求中没有可执行任务。",
                    }
                )
                await asyncio.sleep(0.05)
                continue

            main_batch_running = True
            get_ui_logger().log_info(
                f"Main process accepted batch run {run_id} with {len(requests)} requests."
            )

            def on_progress(done: int, total: int) -> None:
                send_to_branch(
                    {
                        "type": MAIN_BATCH_PROGRESS,
                        "run_id": run_id,
                        "done": done,
                        "total": total,
                        "status_text": f"批处理执行中 {done}/{total}",
                    }
                )

            try:
                summary = await batch_executor.run(requests=requests, on_progress=on_progress)
                first_error = summary.errors[0] if summary.errors else ""
                send_to_branch(
                    {
                        "type": MAIN_BATCH_FINISHED,
                        "run_id": run_id,
                        "summary": summary.to_dict(),
                        "first_error": first_error,
                    }
                )
            except Exception as exc:
                get_ui_logger().log_error(f"Main batch run failed: {exc}")
                send_to_branch(
                    {
                        "type": MAIN_BATCH_REJECTED,
                        "run_id": run_id,
                        "reason": "execution_error",
                        "message": f"主进程执行失败: {exc}",
                    }
                )
            finally:
                main_batch_running = False

    setattr(page, "open_batch_editor", open_batch_editor)
    page.run_task(listen_branch_requests)

    # 2. 窗口初始配置
    page.window.width = 1500
    page.window.height = 950
    page.window.min_width = 1200
    page.window.min_height = 800

    # 3. 实例化布局
    layout = AppLayout(page, state, persistence)
    setattr(page, "app_layout", layout)
    page.render(lambda: layout.build(state.layout_vm))
