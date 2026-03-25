from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import flet as ft

from ui.components.universe.run.console_log import ConsoleLog
from ui.theme import GenshinTheme

if TYPE_CHECKING:
    from ui.states.batch_run_state import BatchRunState


@ft.component
def ActionDrawer(
    state: BatchRunState,
    on_stop: Callable[[], None] | None = None,
    on_back: Callable[[], None] | None = None,
    on_analysis: Callable[[], None] | None = None,
):
    """底部操作栏组件。

    常态下显示操作按钮行（停止、返回编辑、查看分析）。
    日志以底部抽屉形式弹出。
    """
    # 操作按钮行
    button_row = ft.Row(
        [
            # 停止按钮
            ft.TextButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.STOP_CIRCLE_OUTLINED, size=18),
                        ft.Text("停止", size=12),
                    ],
                    spacing=6,
                ),
                on_click=lambda _: on_stop() if on_stop else None,
                style=ft.ButtonStyle(
                    color=ft.Colors.RED_300 if state.is_running else ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                disabled=not state.is_running,
            ),
            ft.Container(expand=True),
            # 返回编辑按钮
            ft.TextButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.EDIT_OUTLINED, size=18),
                        ft.Text("返回编辑", size=12),
                    ],
                    spacing=6,
                ),
                on_click=lambda _: on_back() if on_back else None,
                style=ft.ButtonStyle(
                    color=GenshinTheme.TEXT_SECONDARY,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
            # 查看分析按钮
            ft.TextButton(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=18),
                        ft.Text("查看分析", size=12),
                    ],
                    spacing=6,
                ),
                on_click=lambda _: on_analysis() if on_analysis else None,
                style=ft.ButtonStyle(
                    color=GenshinTheme.PRIMARY,
                    bgcolor=ft.Colors.with_opacity(0.08, GenshinTheme.PRIMARY),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
                disabled=state.is_running or state.total_count == 0,
            ),
            # 日志按钮
            ft.IconButton(
                ft.Icons.TERMINAL,
                icon_color=GenshinTheme.TEXT_SECONDARY if not state.console_visible else GenshinTheme.PRIMARY,
                icon_size=20,
                tooltip="查看日志",
                on_click=lambda _: state.toggle_console(),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    shape=ft.RoundedRectangleBorder(radius=10),
                ),
            ),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 主容器（按钮行）
    main_container = ft.Container(
        content=button_row,
        padding=ft.Padding.symmetric(horizontal=20, vertical=10),
        bgcolor=GenshinTheme.SURFACE,
        border=ft.Border(
            top=ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))
        ),
    )

    # 日志抽屉
    console_drawer = ft.Container(
        content=ConsoleLog(state),
        bgcolor=GenshinTheme.SURFACE_VARIANT,
        border_radius=ft.BorderRadius(top_left=12, top_right=12, bottom_left=0, bottom_right=0),
        border=ft.Border(
            top=ft.BorderSide(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
        ),
        bottom=60,  # 位于按钮行上方
        left=0,
        right=0,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        opacity=1.0 if state.console_visible else 0.0,
        visible=state.console_visible,
    )

    return ft.Stack(
        [
            console_drawer,
            ft.Container(
                content=main_container,
                bottom=0,
                left=0,
                right=0,
            ),
        ],
        expand=True,
    )
