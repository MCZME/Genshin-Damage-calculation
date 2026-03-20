from __future__ import annotations

import json
import multiprocessing

import flet as ft

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

    setattr(page, "open_batch_editor", open_batch_editor)

    # 2. 窗口初始配置
    page.window.width = 1500
    page.window.height = 950
    page.window.min_width = 1200
    page.window.min_height = 800

    # 3. 实例化布局
    layout = AppLayout(page, state, persistence)
    setattr(page, "app_layout", layout)
    page.render(lambda: layout.build(state.layout_vm))
