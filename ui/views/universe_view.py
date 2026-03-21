from __future__ import annotations

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
        modal_mode, set_modal_mode = ft.use_state(None)
        save_name, set_save_name = ft.use_state(project.name)

        header = EditorHeader(
            project_name=project.name,
            leaf_count=state.leaf_count,
            is_running=state.is_running,
            on_save=lambda _: set_modal_mode("save"),
            on_load=lambda _: set_modal_mode("load"),
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

        overlay = self._build_modal(
            state, modal_mode, set_modal_mode, save_name, set_save_name
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
                    overlay,
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

    def _build_modal(
        self,
        state: BatchEditorState,
        modal_mode,
        set_modal_mode,
        save_name,
        set_save_name,
    ):
        dialog = None
        if modal_mode == "save":
            dialog = ft.Container(
                content=ft.Column(
                    [
                        ft.Text("保存批处理项目", size=18, weight=ft.FontWeight.BOLD),
                        ft.TextField(
                            label="文件名",
                            value=save_name,
                            on_change=lambda e: set_save_name(e.control.value),
                        ),
                        ft.ElevatedButton(
                            "保存",
                            bgcolor=GenshinTheme.PRIMARY,
                            color=ft.Colors.WHITE,
                            on_click=lambda _: [
                                state.save_project(save_name or state.project.name),
                                set_modal_mode(None),
                            ],
                        ),
                    ],
                    spacing=16,
                    tight=True,
                ),
                width=420,
                padding=24,
                bgcolor=GenshinTheme.SURFACE,
                border_radius=18,
                border=ft.Border.all(1, GenshinTheme.GLASS_BORDER),
            )
        elif modal_mode == "load":
            files = state.list_projects()
            dialog = ft.Container(
                content=ft.Column(
                    [
                        ft.Text("加载批处理项目", size=18, weight=ft.FontWeight.BOLD),
                        ft.Column(
                            [
                                ft.ListTile(
                                    title=ft.Text(filename),
                                    on_click=lambda _, name=filename: [
                                        state.load_project(name),
                                        set_modal_mode(None),
                                    ],
                                )
                                for filename in files
                            ],
                            spacing=6,
                            scroll=ft.ScrollMode.AUTO,
                            height=300,
                        ),
                    ],
                    spacing=16,
                ),
                width=460,
                padding=24,
                bgcolor=GenshinTheme.SURFACE,
                border_radius=18,
                border=ft.Border.all(1, GenshinTheme.GLASS_BORDER),
            )

        return ft.Container(
            visible=modal_mode is not None,
            expand=True,
            content=ft.Stack(
                [
                    ft.Container(
                        bgcolor=ft.Colors.with_opacity(0.78, ft.Colors.BLACK),
                        on_click=lambda _: set_modal_mode(None),
                    ),
                    ft.Container(content=dialog, alignment=ft.Alignment.CENTER),
                ]
            ),
        )
