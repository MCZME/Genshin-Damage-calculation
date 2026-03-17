from __future__ import annotations
import flet as ft
from typing import Any, cast
from collections.abc import Callable
from ui.theme import GenshinTheme

@ft.component
def PropertySlider(
    label: str,
    value: int,
    min_val: int = 0,
    max_val: int = 100,
    divisions: int | None = None,
    discrete_values: list[int] | None = None,
    element: str = "Neutral",
    on_change: Callable[[int], Any] | None = None,
    on_focus: Callable[[], Any] | None = None,
    slider_key: str = "",
    focused_key: str = "",
):
    """
    声明式属性滑块 (V4.6)。
    修复：
    - 增加 handle_slider_change 的 idx/raw_val 边界校验 (防 IndexError 崩溃)
    - 新增 slider_key / focused_key 互斥机制，确保同一时刻只有一个滑块处于编辑态
    """
    is_edit, set_edit = ft.use_state(False)
    # 局部状态用于滑动时的平滑显示
    local_val, set_local_val = ft.use_state(value)
    elem_color = GenshinTheme.get_element_color(element)

    # 当外部 value 改变时同步局部状态
    ft.use_effect(lambda: set_local_val(value), [value])

    # 互斥机制：如果 focused_key 不等于本滑块 key，强制退出编辑态
    def _check_focus():
        if slider_key and focused_key and focused_key != slider_key and is_edit:
            set_edit(False)

    ft.use_effect(_check_focus, [focused_key])

    def toggle_edit(_: Any):
        if not is_edit and on_focus:
            on_focus()
        set_edit(not is_edit)

    def handle_slider_change(e: Any):
        # 显式从 e.control.value 获取值
        raw_val = float(e.control.value or 0)
        new_val: int
        if discrete_values:
            # [V4.6 Fix] 使用 round() 避免浮点误差，并 clamp 防越界
            idx = int(round(raw_val))
            idx = max(0, min(idx, len(discrete_values) - 1))
            new_val = discrete_values[idx]
        else:
            # [V4.6 Fix] clamp 到合法范围
            new_val = max(min_val, min(max_val, int(round(raw_val))))

        set_local_val(new_val)
        if on_change:
            on_change(new_val)

    # --- 1. 浏览态 ---
    browse_view_controls = cast(list[ft.Control], [
        ft.Text(label, size=11, color=GenshinTheme.TEXT_SECONDARY, weight=ft.FontWeight.W_400),
        ft.Text(str(local_val), size=18, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE)
    ])
    browse_view = ft.Container(
        content=ft.Row(controls=browse_view_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        padding=ft.Padding(12, 0, 12, 0),
        alignment=ft.Alignment(0, 0),
        expand=True
    )

    # --- 2. 编辑态 ---
    slider_val: float = float(local_val)
    s_min: float
    s_max: float
    s_div: int | None

    if discrete_values:
        try:
            slider_val = float(discrete_values.index(local_val))
        except (ValueError, IndexError):
            slider_val = 0.0
        s_min, s_max = 0.0, float(len(discrete_values) - 1)
        s_div = len(discrete_values) - 1 if len(discrete_values) > 1 else None
    else:
        s_min, s_max = float(min_val), float(max_val)
        s_div = divisions

    edit_view_controls = cast(list[ft.Control], [
        ft.Text(label, size=11, weight=ft.FontWeight.BOLD, color=elem_color),
        ft.Slider(
            value=slider_val,
            min=s_min,
            max=s_max,
            divisions=s_div,
            active_color=elem_color,
            expand=True,
            on_change=handle_slider_change
        ),
        ft.Text(str(local_val), size=13, weight=ft.FontWeight.BOLD, width=35, text_align=ft.TextAlign.RIGHT)
    ])
    edit_view = ft.Container(
        content=ft.Row(controls=edit_view_controls, spacing=5),
        padding=ft.Padding(8, 0, 8, 0),
        alignment=ft.Alignment(0, 0),
        expand=True
    )

    # --- 3. 容器组装 ---
    return ft.Container(
        content=ft.AnimatedSwitcher(
            content=edit_view if is_edit else browse_view,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=200,
            switch_in_curve=ft.AnimationCurve.EASE_OUT,
        ),
        width=220,
        height=45,
        border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.08 if is_edit else 0.02, ft.Colors.WHITE),
        border=ft.Border.all(
            1,
            ft.Colors.with_opacity(0.3, elem_color) if is_edit else ft.Colors.with_opacity(0.05, ft.Colors.WHITE)
        ),
        on_click=toggle_edit,
        tooltip=f"Click to edit {label}"
    )
