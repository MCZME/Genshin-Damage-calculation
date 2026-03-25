from __future__ import annotations

import asyncio
import os

import flet as ft

from ui.components.universe import (
    EditorHeader,
    MindMapCanvas,
    NodeInspectorPanel,
)
from ui.states.batch_analysis_state import BatchAnalysisState
from ui.states.batch_editor_state import BatchEditorState
from ui.states.batch_run_state import BatchRunState
from ui.states.batch_universe_state import BatchUniverseState
from ui.theme import GenshinTheme


def _build_canvas_backdrop() -> ft.Control:
    vertical_lines = [
        ft.Container(
            left=120 + index * 220,
            top=100,
            bottom=70,
            width=1,
            bgcolor=ft.Colors.with_opacity(0.035, ft.Colors.WHITE),
        )
        for index in range(8)
    ]
    horizontal_lines = [
        ft.Container(
            left=120,
            right=420,
            top=130 + index * 140,
            height=1,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        )
        for index in range(6)
    ]

    return ft.Stack(
        [
            *vertical_lines,
            *horizontal_lines,
        ],
        expand=True,
    )


async def _on_save(state: BatchEditorState) -> None:
    target_dir = os.path.join(os.getcwd(), "data", "batch_projects")
    os.makedirs(target_dir, exist_ok=True)

    path = await ft.FilePicker().save_file(
        dialog_title="保存批处理项目",
        initial_directory=target_dir,
        file_name=f"{state.project.name or '未命名项目'}.json",
        allowed_extensions=["json"],
    )
    if path:
        state.save_project(path)


async def _on_load(universe_state: BatchUniverseState) -> None:
    target_dir = os.path.join(os.getcwd(), "data", "batch_projects")
    os.makedirs(target_dir, exist_ok=True)

    files: list[ft.FilePickerFile] = await ft.FilePicker().pick_files(
        dialog_title="加载批处理项目",
        initial_directory=target_dir,
        allowed_extensions=["json"],
    )
    if files and len(files) > 0 and files[0].path:
        universe_state.load_project(files[0].path)


async def _on_run_and_navigate(universe_state: BatchUniverseState) -> None:
    """执行批处理并跳转到运行界面。"""
    await universe_state.run_batch()
    # 跳转到运行界面
    if universe_state.editor_state.page:
        await universe_state.editor_state.page.push_route("/run")


@ft.component
def _universe_editor_content(
    editor_state: BatchEditorState,
    run_state: BatchRunState,
    universe_state: BatchUniverseState,
):
    project = editor_state.project

    header = EditorHeader(
        project_name=project.name,
        leaf_count=editor_state.leaf_count,
        is_running=run_state.is_running,
        on_save=lambda e: editor_state.page.run_task(_on_save, editor_state),
        on_load=lambda e: editor_state.page.run_task(_on_load, universe_state),
        on_run=lambda _: editor_state.page.run_task(_on_run_and_navigate, universe_state),
        current_route=editor_state.page.route if editor_state.page else "/",
        on_go_run=lambda _: asyncio.create_task(editor_state.page.push_route("/run")),
        on_go_analysis=lambda _: asyncio.create_task(
            editor_state.page.push_route("/analysis")
        ),
    )

    show_inspector = editor_state.inspector_vm.node_id != "root"
    inspector_panel = ft.Container(
        content=NodeInspectorPanel(
            vm=editor_state.inspector_vm,
            on_rename=editor_state.rename_selected_node,
            on_add_node=lambda parent_id, kind: editor_state.add_child(parent_id, kind),
            on_delete=editor_state.delete_selected_node,
            on_apply_rule=editor_state.update_rule,
            on_apply_range=editor_state.configure_range_anchor
        ),
        visible=show_inspector,
        width=408,
        right=18,
        top=88,
        bottom=18,
        padding=18,
        border_radius=26,
        gradient=ft.LinearGradient(
            begin=ft.Alignment(-1, -1),
            end=ft.Alignment(1, 1),
            colors=[
                ft.Colors.with_opacity(0.93, "#2B243D"),
                ft.Colors.with_opacity(0.93, "#1E192B"),
            ],
        ),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        shadow=[
            ft.BoxShadow(
                blur_radius=26,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.35, ft.Colors.BLACK),
                offset=ft.Offset(0, 10),
            ),
            ft.BoxShadow(
                blur_radius=36,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.14, GenshinTheme.PRIMARY),
                offset=ft.Offset(0, 0),
            ),
        ],
    )

    return ft.Container(
        expand=True,
        bgcolor=GenshinTheme.BACKGROUND,
        content=ft.Stack(
            [
                ft.Container(
                    expand=True,
                    gradient=ft.LinearGradient(
                        begin=ft.Alignment(-1, -1),
                        end=ft.Alignment(1, 1),
                        colors=["#16121F", "#1E1830", "#140F1C"],
                    ),
                ),
                _build_canvas_backdrop(),
                ft.Container(
                    expand=True,
                    content=MindMapCanvas(
                        data=editor_state.canvas_data,
                        on_select=editor_state.select_node,
                        on_add_node=lambda parent_id, kind: editor_state.add_child(
                            parent_id, kind
                        ),
                        on_open_drawer=editor_state.open_add_drawer,
                        on_close_drawer=editor_state.close_add_drawer,
                        on_deselect=lambda: editor_state.select_node("root"),
                    ),
                    padding=ft.Padding(18, 110, 18, 70),
                ),
                header,
                inspector_panel,
            ],
            expand=True,
        ),
    )


class UniverseView(ft.View):
    """批处理编辑器页面视图。"""

    def __init__(
        self,
        editor_state: BatchEditorState,
        run_state: BatchRunState,
        universe_state: BatchUniverseState,
        route: str = "/",
    ) -> None:
        super().__init__(
            route=route,
            controls=[
                _universe_editor_content(
                    editor_state,
                    run_state,
                    universe_state,
                )
            ],
        )
