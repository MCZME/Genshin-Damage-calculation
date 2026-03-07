import flet as ft
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter

@ft.component
def TacticalActionBtn(
    action_key: str,
    label: str,
    element: str = "Neutral",
    on_click = None
):
    """
    声明式战术动作按钮 (V4.5)。
    已修复：回归原子组件视觉规范与交互参数。
    """
    elem_color = GenshinTheme.get_element_color(element)
    
    # 简化显示标签
    short_label = UIFormatter.shorten_action_label(label)
    
    return ft.Container(
        content=ft.Text(short_label, size=12, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
        width=100,
        height=45,
        bgcolor=ft.Colors.with_opacity(0.1, elem_color),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.4, elem_color)),
        border_radius=8,
        alignment=ft.Alignment.CENTER,
        on_click=lambda _: on_click(action_key) if on_click else None,
        tooltip=label,
        animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT)
    )
