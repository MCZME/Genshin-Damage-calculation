from __future__ import annotations

from typing import TYPE_CHECKING

import flet as ft

from ui.theme import GenshinTheme

if TYPE_CHECKING:
    from ui.states.batch_run_state import BatchRunState


@ft.component
def CommandRibbon(state: BatchRunState, project_name: str):
    """顶部命令栏组件。

    全宽玻璃态卡片，包含：
    - 左侧：项目面包屑 + 动态状态
    - 右侧：大字计数器（总数 / 成功 / 失败）
    - 底部：1px 线型进度条
    """
    progress = max(0.0, min(1.0, state.progress))

    # 左侧：面包屑 + 状态
    left_section = ft.Row(
        [
            ft.Icon(ft.Icons.HUB, size=16, color=GenshinTheme.TEXT_SECONDARY),
            ft.Text(
                project_name,
                size=14,
                weight=ft.FontWeight.W_600,
                color=GenshinTheme.ON_SURFACE,
            ),
            ft.Container(
                content=ft.Text(
                    state.status_text,
                    size=12,
                    color=GenshinTheme.TEXT_SECONDARY,
                ),
                padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                border_radius=8,
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            ),
        ],
        spacing=10,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 右侧：计数器
    counter_row = ft.Row(
        [
            _counter_chip(f"{state.total_count}", "总", GenshinTheme.TEXT_SECONDARY),
            ft.Container(width=1, height=16, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            _counter_chip(f"{state.success_count}", "成功", GenshinTheme.GOLD_LIGHT),
            ft.Container(width=1, height=16, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            _counter_chip(f"{state.error_count}", "失败", ft.Colors.RED_300),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # 进度条
    progress_bar = ft.ProgressBar(
        value=progress,
        height=2,
        bar_height=2,
        color=GenshinTheme.PRIMARY,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [left_section, counter_row],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                progress_bar,
            ],
            spacing=12,
        ),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        border_radius=16,
        bgcolor=ft.Colors.with_opacity(0.4, "#322D46"),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        shadow=ft.BoxShadow(
            blur_radius=16,
            spread_radius=0,
            color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ),
    )


def _counter_chip(value: str, label: str, color: str) -> ft.Control:
    """计数器芯片。"""
    return ft.Row(
        [
            ft.Text(
                value,
                size=20,
                weight=ft.FontWeight.W_800,
                color=color,
            ),
            ft.Text(
                label,
                size=10,
                color=GenshinTheme.TEXT_SECONDARY,
            ),
        ],
        spacing=4,
        vertical_alignment=ft.CrossAxisAlignment.END,
    )
