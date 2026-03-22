from __future__ import annotations

import asyncio
import queue
from typing import Any

import flet as ft

from core.batch import (
    MAIN_BATCH_FINISHED,
    MAIN_BATCH_PROGRESS,
    MAIN_BATCH_REJECTED,
)
from ui.states.batch_universe_state import BatchUniverseState
from ui.theme import GenshinTheme
from ui.views.universe_router import UniverseRouter
from ui.views.universe_routes import (
    UNIVERSE_ANALYSIS_ROUTE,
    UNIVERSE_EDITOR_ROUTE,
    UNIVERSE_RUN_ROUTE,
    resolve_universe_route,
)


def build_universe_route_stack(route: str | None) -> list[str]:
    """兼容旧测试的活动路由定义。"""
    return [resolve_universe_route(route)]


def start_universe_process(main_to_branch, branch_to_main=None):
    """批处理编辑器独立进程入口。"""

    def main(page: ft.Page):
        page.title = "批处理编辑器"
        page.window.width = 1360
        page.window.height = 860
        page.window.min_width = 1100
        page.window.min_height = 760
        GenshinTheme.apply_page_settings(page)

        state = BatchUniverseState()
        state.attach_page(page)
        state.attach_branch_queue(branch_to_main)

        async def listen_for_init() -> None:
            while True:
                received_any = False
                while True:
                    try:
                        message: dict[str, Any] = main_to_branch.get_nowait()
                    except queue.Empty:
                        break

                    received_any = True
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
                await asyncio.sleep(0.05 if received_any else 0.2)

        page.run_task(listen_for_init)
        page.route = resolve_universe_route(page.route)
        page.render_views(
            UniverseRouter,
            state,
            state.editor_state,
            state.run_state,
            state.analysis_state,
        )

    ft.run(main, view=ft.AppView.FLET_APP)
