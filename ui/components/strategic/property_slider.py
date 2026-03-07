import flet as ft
from ui.theme import GenshinTheme

@ft.component
def PropertySlider(
    label: str,
    value: int,
    min_val: int = 0,
    max_val: int = 100,
    divisions: int = None,
    discrete_values: list = None,
    element: str = "Neutral",
    on_change = None,
    on_focus = None
):
    """
    声明式属性滑块 (V4.5)。
    已优化：增加局部状态同步以实现极致响应。
    """
    is_edit, set_edit = ft.use_state(False)
    # 局部状态用于滑动时的平滑显示
    local_val, set_local_val = ft.use_state(value)
    elem_color = GenshinTheme.get_element_color(element)

    # 当外部 value 改变时同步局部状态
    ft.use_effect(lambda: set_local_val(value), [value])

    def toggle_edit(_):
        if not is_edit and on_focus:
            on_focus() 
        set_edit(not is_edit)

    def handle_slider_change(e):
        new_val = discrete_values[int(e.control.value)] if discrete_values else int(e.control.value)
        set_local_val(new_val)
        if on_change:
            on_change(new_val)

    # --- 1. 浏览态 ---
    browse_view = ft.Container(
        content=ft.Row([
            ft.Text(label, size=11, color=GenshinTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_400),
            ft.Text(str(local_val), size=18, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding(12, 0, 12, 0), alignment=ft.Alignment.CENTER, expand=True
    )

    # --- 2. 编辑态 ---
    slider_val = local_val
    if discrete_values:
        try: slider_val = discrete_values.index(local_val)
        except: slider_val = 0
        s_min, s_max, s_div = 0, len(discrete_values)-1, len(discrete_values)-1
    else:
        s_min, s_max, s_div = min_val, max_val, divisions

    edit_view = ft.Container(
        content=ft.Row([
            ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=elem_color),
            ft.Slider(
                value=slider_val, min=s_min, max=s_max, divisions=s_div,
                active_color=elem_color, expand=True,
                on_change=handle_slider_change
            ),
            ft.Text(str(local_val), size=13, weight=ft.FontWeight.BOLD, width=35, text_align=ft.TextAlign.RIGHT)
        ], spacing=5),
        padding=ft.Padding(8, 0, 8, 0), alignment=ft.Alignment.CENTER, expand=True
    )

    # --- 3. 容器组装 ---
    return ft.Container(
        content=ft.AnimatedSwitcher(
            content=edit_view if is_edit else browse_view,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=200, switch_in_curve=ft.AnimationCurve.EASE_OUT,
        ),
        width=220, height=45, border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.08 if is_edit else 0.02, ft.Colors.WHITE),
        border=ft.Border.all(
            1, 
            ft.Colors.with_opacity(0.3, elem_color) if is_edit else ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
        ),
        on_click=toggle_edit,
        tooltip=f"Click to edit {label}"
    )
