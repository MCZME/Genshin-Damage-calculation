from __future__ import annotations
import flet as ft
from typing import Any
from collections.abc import Callable

@ft.component
def TargetSidebarSlot(
    index: int, 
    target: dict[str, Any], 
    is_selected: bool = False,
    on_click: Callable[[int], Any] | None = None,
    on_remove: Callable[[int], Any] | None = None
):
    """
    声明式敌方目标侧边栏槽位 (V4.5)。
    """
    theme_color = ft.Colors.RED_400 if is_selected else ft.Colors.RED_900
    bg_opacity = 0.28 if is_selected else 0.10
    
    avatar = ft.Container(
        content=ft.Text(str(index + 1), size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
        width=36, 
        height=36, 
        bgcolor=ft.Colors.with_opacity(0.3, theme_color),
        border_radius=18, 
        alignment=ft.Alignment.CENTER,
        border=ft.Border.all(1.5, ft.Colors.with_opacity(0.6 if is_selected else 0.25, theme_color))
    )

    name_col_controls: list[ft.Control] = [
        ft.Text(str(target.get('name', 'Unknown')), size=13, weight=ft.FontWeight.W_900 if is_selected else ft.FontWeight.BOLD),
        ft.Text(f"Lv.{target.get('level', 1)}", size=10, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
    ]
    name_col = ft.Column(controls=name_col_controls, spacing=1, expand=True)

    remove_btn = ft.GestureDetector(
        content=ft.Container(
            content=ft.Icon(ft.Icons.CLOSE, size=11, color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
            width=22, 
            height=22, 
            border_radius=11, 
            alignment=ft.Alignment.CENTER,
            on_click=lambda _: on_remove(index) if on_remove else None,
        ),
        mouse_cursor=ft.MouseCursor.CLICK
    )

    row_controls: list[ft.Control] = [avatar, name_col, remove_btn]
    
    stack_controls: list[ft.Control] = [
        ft.Container(
            expand=True, 
            border_radius=12,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), 
                end=ft.Alignment(1, 1),
                colors=[
                    ft.Colors.with_opacity(bg_opacity, theme_color), 
                    ft.Colors.with_opacity(bg_opacity * 0.3, theme_color)
                ]
            )
        ),
        ft.Container(
            content=ft.Row(
                controls=row_controls, 
                spacing=9, 
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding(11, 11, 11, 11)
        )
    ]

    return ft.GestureDetector(
        content=ft.Container(
            content=ft.Stack(controls=stack_controls),
            height=60, 
            border_radius=12,
            border=ft.Border.all(2 if is_selected else 1, ft.Colors.with_opacity(0.65 if is_selected else 0.12, theme_color)),
            shadow=[ft.BoxShadow(
                spread_radius=1, 
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.5, theme_color)
            )] if is_selected else None,
            on_click=lambda _: on_click(index) if on_click else None,
            offset=ft.Offset(0.04, 0) if is_selected else ft.Offset(0, 0),
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
        ),
        mouse_cursor=ft.MouseCursor.CLICK
    )
