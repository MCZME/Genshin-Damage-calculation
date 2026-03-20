from __future__ import annotations

import flet as ft

from ui.theme import GenshinTheme


@ft.component
def EditorHeader(
    project_name: str,
    leaf_count: int,
    is_running: bool,
    on_save,
    on_load,
    on_run,
):
    return ft.Container(
        top=0,
        left=0,
        right=0,
        height=82,
        alignment=ft.Alignment.CENTER_LEFT,
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(
                                ft.Icons.ACCOUNT_TREE_ROUNDED,
                                color=GenshinTheme.ON_PRIMARY,
                                size=22,
                            ),
                            width=46,
                            height=46,
                            border_radius=14,
                            bgcolor=GenshinTheme.PRIMARY,
                            alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    project_name,
                                    size=20,
                                    weight=ft.FontWeight.W_900,
                                    color=GenshinTheme.ON_SURFACE,
                                ),
                                ft.Text(
                                    f"思维导图模式 | 叶子任务 {leaf_count}",
                                    size=11,
                                    color=GenshinTheme.TEXT_SECONDARY,
                                ),
                            ],
                            spacing=3,
                        ),
                    ],
                    spacing=14,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            ft.Icons.SAVE_OUTLINED,
                            tooltip="保存批处理项目",
                            on_click=on_save,
                        ),
                        ft.IconButton(
                            ft.Icons.FOLDER_OPEN_OUTLINED,
                            tooltip="加载批处理项目",
                            on_click=on_load,
                        ),
                        ft.ElevatedButton(
                            "执行批处理",
                            icon=ft.Icons.PLAY_ARROW_ROUNDED,
                            bgcolor=GenshinTheme.PRIMARY,
                            color=ft.Colors.WHITE,
                            disabled=is_running,
                            on_click=on_run,
                        ),
                    ],
                    spacing=10,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=28, vertical=18),
        bgcolor="rgba(25, 21, 37, 0.86)",
        border=ft.border.only(bottom=ft.BorderSide(1, "rgba(255,255,255,0.06)")),
    )
