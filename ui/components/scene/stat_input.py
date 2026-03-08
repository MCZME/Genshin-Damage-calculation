from __future__ import annotations
import flet as ft
from typing import Any
from collections.abc import Callable
from ui.theme import GenshinTheme

@ft.component
def StatInputField(
    label: str,
    value: str = "0",
    suffix: str = "",
    element: str = "Neutral",
    icon: ft.IconData | None = None,
    on_select: Callable[[str], Any] | None = None,
    on_label_change: Callable[[str], Any] | None = None,
    label_options: list[str] | None = None,
    width: float = 120
):
    """
    声明式属性输入框 (V5.0)。
    已修复：优化文本溢出显示与布局比例。
    """
    is_focused, set_focused = ft.use_state(False)
    elem_color = GenshinTheme.get_element_color(element)
    
    # 1. 标签部分 (适配长文本)
    label_ctrl: ft.Control
    if label_options:
        label_ctrl = ft.Dropdown(
            value=label,
            options=[ft.dropdown.Option(opt) for opt in label_options],
            dense=True, 
            text_size=11, 
            width=115, # 增加宽度以完整显示“元素充能效率%”
            border=ft.InputBorder.NONE,
            content_padding=ft.Padding(0, 0, 0, 0),
            on_select=lambda e: on_label_change(e.control.value or "") if on_label_change else None
        )

    else:
        label_ctrl = ft.Text(
            label, 
            size=10, 
            color=GenshinTheme.TEXT_SECONDARY, 
            weight=ft.FontWeight.W_400, 
            style=ft.TextStyle(letter_spacing=0.5)
        )

    # 2. 输入控件 (对齐与比例优化)
    tf = ft.TextField(
        value=value,
        suffix=ft.Text(suffix, size=11, color=GenshinTheme.TEXT_SECONDARY) if suffix else None,
        dense=True, 
        content_padding=ft.Padding(5, 10, 5, 10), 
        border=ft.InputBorder.NONE,
        cursor_color=elem_color, 
        cursor_width=1,
        text_style=ft.TextStyle(size=13, color=GenshinTheme.ON_SURFACE, weight=ft.FontWeight.W_700),
        on_change=lambda e: on_select(e.control.value or "") if on_select else None,
        on_focus=lambda _: set_focused(True),
        on_blur=lambda _: set_focused(False),
        text_align=ft.TextAlign.RIGHT,
        expand=True # 自动填充剩余空间
    )

    icon_ctrl = ft.Icon(icon, size=14, color=ft.Colors.with_opacity(0.5, elem_color)) if icon else None

    # 3. 容器组装 (使用 SpaceBetween 确保两端对齐)
    items: list[ft.Control] = []
    if icon_ctrl:
        items.append(icon_ctrl)
    items.append(label_ctrl)
    items.append(tf)

    return ft.Container(
        content=ft.Row(
            controls=items, 
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN, 
            vertical_alignment=ft.CrossAxisAlignment.CENTER, 
            spacing=0
        ),
        width=width, 
        height=38, 
        padding=ft.Padding(10, 0, 10, 0), 
        border_radius=6,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        border=ft.Border.all(
            1.5 if is_focused else 1, 
            elem_color if is_focused else ft.Colors.with_opacity(0.2, GenshinTheme.ON_SURFACE)
        ),
        shadow=[GenshinTheme.get_element_glow(element, intensity=0.6)] if is_focused else None,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
    )
