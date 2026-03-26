"""开关配置项组件。"""
from __future__ import annotations

import flet as ft
from typing import Any, Callable

from ui.theme import GenshinTheme


@ft.component
def ConfigSwitchItem(
    label: str,
    description: str,
    value: bool,
    on_change: Callable[[bool], Any],
) -> ft.Control:
    """
    开关配置项组件。

    Args:
        label: 配置项标签
        description: 配置项描述
        value: 当前值
        on_change: 值变更回调
    """
    return ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(
                            label,
                            size=13,
                            weight=ft.FontWeight.W_500,
                            color=GenshinTheme.ON_SURFACE,
                        ),
                        ft.Text(
                            description,
                            size=10,
                            color=GenshinTheme.TEXT_SECONDARY,
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
                ft.Switch(
                    value=value,
                    on_change=lambda e: on_change(bool(e.control.value)),
                    active_track_color=GenshinTheme.PRIMARY,
                    active_color=GenshinTheme.ON_PRIMARY,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(12, 8, 12, 8),
        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        border_radius=8,
    )
