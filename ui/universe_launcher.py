from __future__ import annotations

import asyncio
from typing import Any

import flet as ft

from core.batch import (
    MAIN_BATCH_FINISHED,
    MAIN_BATCH_PROGRESS,
    MAIN_BATCH_REJECTED,
)
from ui.states.batch_editor_state import BatchEditorState
from ui.theme import GenshinTheme
from ui.views.universe_view import UniverseView


def start_universe_process(main_to_branch, branch_to_main=None):
    """批处理编辑器独立进程入口。"""

    def main(page: ft.Page):
        page.title = "批处理编辑器"
        page.window.width = 1360
        page.window.height = 860
        page.window.min_width = 1100
        page.window.min_height = 760
        GenshinTheme.apply_page_settings(page)

        state = BatchEditorState()
        state.page = page
        state.branch_to_main_queue = branch_to_main
        view = UniverseView()

        async def listen_for_init() -> None:
            while True:
                if not main_to_branch.empty():
                    message: dict[str, Any] = main_to_branch.get()
                    msg_type = message.get("type")
                    if msg_type == "INIT_BATCH_EDITOR":
                        state.initialize_project(
                            message.get("config", {}),
                            message.get("project_name", "批处理项目"),
                        )
                    elif msg_type in {
                        MAIN_BATCH_PROGRESS,
                        MAIN_BATCH_FINISHED,
                        MAIN_BATCH_REJECTED,
                    }:
                        state.handle_main_message(message)
                await asyncio.sleep(0.3)

        page.run_task(listen_for_init)
        page.render(lambda: view.build(state))

    ft.run(main, view=ft.AppView.FLET_APP)
