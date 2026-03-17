import flet as ft
from ui.theme import GenshinTheme
from ui.view_models.tactical.action_vm import ActionViewModel

@ft.component
def ActionCard(
    vm: ActionViewModel,
    index: int,
    char_name: str,
    element: str = "Neutral",
    is_selected: bool = False,
    on_click = None,
    on_delete = None
):
    """
    声明式动作卡片 (MVVM V5.0)。
    在战术时间轴中显示动作胶囊。
    """
    is_hovered, set_is_hovered = ft.use_state(False)
    elem_color = GenshinTheme.get_element_color(element)
    display_name = vm.get_display_label()
    
    # 背景渐变
    bg_opacity = 0.25 if is_selected else 0.08
    bg_gradient = ft.LinearGradient(
        begin=ft.Alignment(-1, -1),
        end=ft.Alignment(1, 1),
        colors=[
            ft.Colors.with_opacity(bg_opacity, elem_color),
            ft.Colors.with_opacity(bg_opacity * 0.4, elem_color),
        ]
    )

    return ft.Container(
        content=ft.Stack([
            # 背景渐变层
            ft.Container(expand=True, gradient=bg_gradient, border_radius=12),
            # 文字内容层
            ft.Column([
                ft.Text(
                    char_name if char_name else "??", 
                    size=7, weight=ft.FontWeight.W_600, 
                    color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS
                ),
                ft.Text(
                    display_name, 
                    size=16, weight=ft.FontWeight.W_900, 
                    color=ft.Colors.WHITE,
                    no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS
                ),
            ], spacing=-2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            
            # 右上角微型状态标识 (选中时增加一个光点)
            ft.Container(
                content=ft.CircleAvatar(radius=2, bgcolor=elem_color) if is_selected else None,
                alignment=ft.Alignment.TOP_RIGHT,
                padding=ft.Padding(0, 6, 6, 0),
            ),

            # 左上角删除按钮 (悬浮显示)
            ft.Container(
                content=ft.Icon(ft.Icons.CLOSE, size=10, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_ACCENT_700,
                width=16,
                height=16,
                border_radius=8,
                alignment=ft.Alignment.CENTER,
                visible=is_hovered,
                on_click=lambda e: on_delete(index) if on_delete else None,
                left=4,
                top=4,
            )
        ], alignment=ft.Alignment.CENTER),
        width=80,
        height=55,
        border_radius=12,
        border=ft.Border.all(
            2 if is_selected else 1, 
            ft.Colors.with_opacity(0.6 if is_selected else 0.15, elem_color)
        ),
        shadow=GenshinTheme.get_element_glow(element, 0.4) if is_selected else None,
        on_click=lambda _: on_click(index) if on_click else None,
        on_hover=lambda e: [set_is_hovered(e.data == True)],
        scale=1.05 if is_selected else 1.0,
        animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
    )
