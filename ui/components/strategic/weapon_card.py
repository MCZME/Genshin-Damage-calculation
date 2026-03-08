from __future__ import annotations
import flet as ft
from typing import Any
from collections.abc import Callable
from ui.components.strategic.property_slider import PropertySlider
from ui.view_models.strategic.weapon_vm import WeaponViewModel

@ft.component
def WeaponCard(
    vm: WeaponViewModel, 
    element: str = "Neutral",
    on_picker_click: Callable[[], Any] | None = None,
    on_slider_focus: Callable[[], Any] | None = None
):
    """
    声明式武器配置卡组件 (MVVM V5.0)。
    直接绑定到 WeaponViewModel。
    """
    is_empty = not vm.name
    
    # 1. 武器预览区域
    # TODO: 以后可以从 VM 获取真实的武器图标路径
    icon_ctrl = ft.Icon(ft.Icons.SHIELD if is_empty else ft.Icons.HARDWARE, size=30, color=ft.Colors.WHITE_24)
    
    weapon_preview = ft.Container(
        content=icon_ctrl,
        width=80, 
        height=80,
        bgcolor=ft.Colors.BLACK_26,
        border_radius=8,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        alignment=ft.Alignment(0, 0),
        on_click=lambda _: on_picker_click() if on_picker_click else None,
    )

    # 2. 布局组装
    col_controls: list[ft.Control] = [
        ft.Text(vm.display_name, size=12, weight=ft.FontWeight.BOLD),
        # 使用 PropertySlider 绑定 VM
        PropertySlider(
            "精炼", 
            value=vm.refinement, 
            min_val=1, 
            max_val=5, 
            divisions=4, 
            element=element, 
            on_change=vm.set_refinement,
            on_focus=on_slider_focus
        ),
        PropertySlider(
            "等级", 
            value=vm.level, 
            discrete_values=[1, 20, 40, 50, 60, 70, 80, 90], 
            element=element, 
            on_change=vm.set_level,
            on_focus=on_slider_focus
        ),
    ]

    main_col_controls: list[ft.Control] = [
        ft.Text("武器装备", size=14, weight=ft.FontWeight.BOLD, opacity=0.6),
        ft.Row(
            controls=[
                weapon_preview,
                ft.Column(controls=col_controls, spacing=5)
            ], 
            spacing=15
        )
    ]

    return ft.Container(
        content=ft.Column(controls=main_col_controls, spacing=10),
        padding=ft.Padding(20, 15, 20, 15),
        bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
        border_radius=12,
        width=380
    )
