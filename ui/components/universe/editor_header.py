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
    current_route: str = "/",
    on_go_run=None,
    on_go_analysis=None,
):
    nav_group = ft.Row(
        [
            ft.OutlinedButton(
                content=ft.Text("运行视图"),
                icon=ft.Icons.PLAY_CIRCLE_OUTLINED,
                disabled=on_go_run is None or current_route == "/run",
                on_click=on_go_run,
                style=ft.ButtonStyle(
                    bgcolor=(
                        ft.Colors.with_opacity(0.18, GenshinTheme.PRIMARY)
                        if current_route == "/run"
                        else ft.Colors.with_opacity(0.04, ft.Colors.WHITE)
                    ),
                    side=ft.BorderSide(
                        1,
                        (
                            ft.Colors.with_opacity(0.7, GenshinTheme.PRIMARY)
                            if current_route == "/run"
                            else ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
                        ),
                    ),
                ),
            ),
            ft.OutlinedButton(
                content=ft.Text("分析视图"),
                icon=ft.Icons.QUERY_STATS_OUTLINED,
                disabled=on_go_analysis is None or current_route == "/analysis",
                on_click=on_go_analysis,
                style=ft.ButtonStyle(
                    bgcolor=(
                        ft.Colors.with_opacity(0.18, GenshinTheme.PRIMARY)
                        if current_route == "/analysis"
                        else ft.Colors.with_opacity(0.04, ft.Colors.WHITE)
                    ),
                    side=ft.BorderSide(
                        1,
                        (
                            ft.Colors.with_opacity(0.7, GenshinTheme.PRIMARY)
                            if current_route == "/analysis"
                            else ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
                        ),
                    ),
                ),
            ),
        ],
        spacing=8,
    )

    return ft.Container(
        top=0,
        left=0,
        right=0,
        height=92,
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
                        nav_group,
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
                        ft.Button(
                            "执行批处理",
                            icon=ft.Icons.PLAY_ARROW_ROUNDED,
                            bgcolor=GenshinTheme.PRIMARY,
                            color=ft.Colors.WHITE,
                            disabled=is_running,
                            on_click=on_run,
                        ),
                    ],
                    spacing=12,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding.symmetric(horizontal=28, vertical=18),
        bgcolor="rgba(25, 21, 37, 0.86)",
        border=ft.Border.only(bottom=ft.BorderSide(1, "rgba(255,255,255,0.06)")),
    )
