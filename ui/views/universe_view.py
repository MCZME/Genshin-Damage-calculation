from __future__ import annotations

import os

import flet as ft

from ui.components.universe import (
    EditorHeader,
    MindMapCanvas,
    NodeInspectorPanel,
)
from ui.states.batch_editor_state import BatchEditorState
from ui.theme import GenshinTheme


class UniverseView:
    """批处理编辑器视图，采用思维导图式树布局。"""

    @ft.component
    def build(self, state: BatchEditorState):
        project = state.project

        header = EditorHeader(
            project_name=project.name,
            leaf_count=state.leaf_count,
            is_running=state.is_running,
            on_save=lambda e: state.page.run_task(self._on_save, state),
            on_load=lambda e: state.page.run_task(self._on_load, state),
            on_run=lambda _: state.page.run_task(state.run_batch),
        )

        show_inspector = state.inspector_vm.node_id != "root"
        inspector_panel = ft.Container(
            content=NodeInspectorPanel(
                vm=state.inspector_vm,
                on_rename=state.rename_selected_node,
                on_add_node=lambda parent_id, kind: state.add_child(parent_id, kind),
                on_delete=state.delete_selected_node,
                on_apply_rule=state.update_rule,
                on_apply_range=state.configure_range_anchor,
                last_summary=state.last_summary,
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
                    self._build_canvas_backdrop(),
                    ft.Container(
                        expand=True,
                        content=MindMapCanvas(
                            data=state.canvas_data,
                            on_select=state.select_node,
                            on_add_node=lambda parent_id, kind: state.add_child(parent_id, kind),
                            on_open_drawer=state.open_add_drawer,
                            on_close_drawer=state.close_add_drawer,
                            on_deselect=lambda: state.select_node("root"),
                        ),
                        padding=ft.Padding(18, 110, 18, 70),
                    ),
                    header,
                    inspector_panel,
                ],
                expand=True,
            ),
        )

    def _build_canvas_backdrop(self) -> ft.Control:
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

    async def _on_save(self, state: BatchEditorState) -> None:
        """保存文件 - 使用 FilePicker。"""
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

    async def _on_load(self, state: BatchEditorState) -> None:
        """加载文件 - 使用 FilePicker。"""
        target_dir = os.path.join(os.getcwd(), "data", "batch_projects")
        os.makedirs(target_dir, exist_ok=True)

        files: list[ft.FilePickerFile] = await ft.FilePicker().pick_files(
            dialog_title="加载批处理项目",
            initial_directory=target_dir,
            allowed_extensions=["json"],
        )

        if files and len(files) > 0:
            if files[0].path:
                state.load_project(files[0].path)
