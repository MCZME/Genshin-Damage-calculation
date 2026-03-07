import flet as ft
from ui.theme import GenshinTheme

@ft.component
def TacticalMemberSlot(
    index: int,
    member: dict,
    is_selected: bool = False,
    on_click = None
):
    """
    声明式战术视图成员槽位 (V4.5)。
    已修复：回归原子组件视觉规范与交互参数。
    """
    is_empty = member.get("id") is None
    elem_color = GenshinTheme.get_element_color(member.get("element", "Neutral"))
    
    if is_empty:
        return ft.Container(
            content=ft.Text("未配置角色", size=11, color=ft.Colors.WHITE_24),
            height=60,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE))
        )

    bg_opacity = 0.28 if is_selected else 0.10
    avatar = ft.Container(
        content=ft.Text(member.get("name", "?")[0], size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
        width=36, height=36, bgcolor=ft.Colors.with_opacity(0.3, elem_color),
        border_radius=18, alignment=ft.Alignment.CENTER,
        border=ft.Border.all(1.5, ft.Colors.with_opacity(0.6 if is_selected else 0.25, elem_color))
    )

    return ft.Container(
        content=ft.Row([
            avatar,
            ft.Column([
                ft.Text(member.get("name", "未选定"), size=13, weight=ft.FontWeight.W_900 if is_selected else ft.FontWeight.BOLD),
                ft.Text(member.get("element", "Neutral"), size=10, opacity=0.5),
            ], spacing=1, expand=True)
        ], spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding(11, 11, 11, 11),
        height=60,
        border_radius=12,
        bgcolor=ft.Colors.with_opacity(bg_opacity, elem_color),
        border=ft.Border.all(2 if is_selected else 1, ft.Colors.with_opacity(0.65 if is_selected else 0.12, elem_color)),
        on_click=lambda _: on_click(index) if on_click else None,
        offset=ft.Offset(0.04, 0) if is_selected else ft.Offset(0, 0),
        animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
        tooltip=member.get("name")
    )
