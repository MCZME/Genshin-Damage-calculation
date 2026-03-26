"""文本输入配置项组件。"""
from __future__ import annotations

import flet as ft
from typing import Any, Callable, Optional

from ui.theme import GenshinTheme


@ft.component
def ConfigTextItem(
    label: str,
    value: str,
    on_change: Callable[[str], Any],
    password: bool = False,
    can_reveal: bool = False,
    keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT,
    width: Optional[float] = None,
) -> ft.Control:
    """
    文本输入配置项组件。

    Args:
        label: 配置项标签
        value: 当前值
        on_change: 值变更回调
        password: 是否为密码字段
        can_reveal: 是否允许显示密码
        keyboard_type: 键盘类型
        width: 组件宽度
    """
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    label,
                    size=12,
                    weight=ft.FontWeight.W_500,
                    color=GenshinTheme.TEXT_SECONDARY,
                ),
                ft.TextField(
                    value=value,
                    on_change=lambda e: on_change(e.control.value or ""),
                    password=password,
                    can_reveal_password=can_reveal,
                    keyboard_type=keyboard_type,
                    dense=True,
                    text_size=13,
                    border_color=ft.Colors.WHITE_24,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    cursor_color=GenshinTheme.PRIMARY,
                    expand=True,
                ),
            ],
            spacing=4,
        ),
        padding=ft.Padding(12, 8, 12, 8),
        bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        border_radius=8,
        width=width,
    )
