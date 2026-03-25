from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from ui.theme import GenshinTheme

if TYPE_CHECKING:
    from ui.states.batch_run_state import BatchRunState


@ft.component
def ConsoleLog(state: BatchRunState):
    """控制台日志组件。

    展示日志列表，支持自动滚动和错误高亮。
    """
    log_items: list[ft.Control] = []

    for log in state.console_logs:
        is_error = log.startswith("[ERROR]")
        is_info = log.startswith("[INFO]")

        text_color: str
        bg_color: str

        if is_error:
            text_color = ft.Colors.RED_300
            bg_color = ft.Colors.with_opacity(0.08, ft.Colors.RED_400)
        elif is_info:
            text_color = ft.Colors.BLUE_300
            bg_color = ft.Colors.TRANSPARENT
        else:
            text_color = GenshinTheme.TEXT_SECONDARY
            bg_color = ft.Colors.TRANSPARENT

        log_items.append(
            ft.Container(
                content=ft.Text(
                    log,
                    size=11,
                    color=text_color,
                    font_family="monospace",
                    selectable=True,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=4,
                bgcolor=bg_color,
            )
        )

    if not log_items:
        log_items.append(
            ft.Container(
                content=ft.Text(
                    "暂无日志",
                    size=11,
                    color=GenshinTheme.TEXT_SECONDARY,
                ),
                padding=ft.Padding.all(8),
            )
        )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.TERMINAL,
                            size=14,
                            color=GenshinTheme.TEXT_SECONDARY,
                        ),
                        ft.Text(
                            "执行日志",
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color=GenshinTheme.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=6,
                ),
                ft.Container(
                    content=ft.Column(
                        log_items,
                        spacing=2,
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                    border_radius=8,
                    padding=ft.Padding.all(8),
                    expand=True,
                ),
            ],
            spacing=8,
            expand=True,
        ),
        padding=ft.Padding.all(12),
        height=200,
    )
