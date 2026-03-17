from __future__ import annotations
import flet as ft
from typing import Any
from collections.abc import Callable
from ui.theme import GenshinTheme
from ui.view_models.strategic.character_vm import CharacterViewModel

@ft.component
def MemberSlot(
    vm: CharacterViewModel,
    index: int,
    is_selected: bool = False,
    on_click: Callable[[int], Any] | None = None,
    on_remove: Callable[[int], Any] | None = None,
    on_add: Callable[[int], Any] | None = None
):
    """
    编队成员槽位组件 (MVVM V5.0)。
    直接绑定到 CharacterViewModel。
    """
    is_empty = vm.is_empty
    elem_color = GenshinTheme.get_element_color(vm.element)

    # 1. 处理空状态
    if is_empty:
        empty_controls: list[ft.Control] = [
            ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, color=ft.Colors.WHITE_24, size=28),
            ft.Text("添加角色", size=11, color=ft.Colors.WHITE_24, weight=ft.FontWeight.W_500)
        ]
        return ft.Container(
            content=ft.Column(
                controls=empty_controls, 
                alignment=ft.MainAxisAlignment.CENTER, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                spacing=6
            ),
            alignment=ft.Alignment(0, 0),
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
            border_radius=12,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
            on_click=lambda _: on_add(index) if on_add else None,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE)
        )

    # 2. 视觉参数
    bg_opacity = 0.28 if is_selected else 0.10
    border_w = 2 if is_selected else 1
    border_alpha = 0.65 if is_selected else 0.12

    # --- 内部组件工厂 ---
    def create_mini_talent_tag(label: str, val: int) -> ft.Control:
        talent_tag_controls: list[ft.Control] = [
            ft.Text(label, size=9, weight=ft.FontWeight.W_900, color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE)),
            ft.Text(str(val), size=13, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
        ]
        return ft.Container(
            content=ft.Column(
                controls=talent_tag_controls, 
                spacing=0, 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=ft.Colors.with_opacity(0.35, ft.Colors.BLACK),
            padding=ft.Padding(7, 4, 7, 4),
            border_radius=6,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
        )

    # 3. 布局构建
    avatar = ft.Container(
        content=ft.Text(vm.name[0] if vm.name else "?", size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
        width=36, 
        height=36,
        bgcolor=ft.Colors.with_opacity(0.3, elem_color),
        border_radius=18,
        alignment=ft.Alignment(0, 0),
        border=ft.Border.all(1.5, ft.Colors.with_opacity(0.25, elem_color))
    )
    
    remove_btn = ft.Container(
        content=ft.Icon(ft.Icons.CLOSE, size=12, color=ft.Colors.with_opacity(0.28, ft.Colors.WHITE)),
        width=22, 
        height=22, 
        border_radius=11, 
        alignment=ft.Alignment(0, 0),
        on_click=lambda _: on_remove(index) if on_remove else None,
    )

    name_col_controls: list[ft.Control] = [
        ft.Text(
            vm.name, 
            size=13, 
            weight=ft.FontWeight.W_900 if is_selected else ft.FontWeight.BOLD,
            color=ft.Colors.with_opacity(1.0 if is_selected else 0.75, ft.Colors.WHITE),
            no_wrap=True, 
            overflow=ft.TextOverflow.ELLIPSIS
        ),
        ft.Text(f"Lv.{vm.level}  C{vm.constellation}", size=10, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE))
    ]
    
    top_row_controls: list[ft.Control] = [
        avatar, 
        ft.Column(controls=name_col_controls, spacing=1, expand=True),
        remove_btn
    ]
    top_row = ft.Row(controls=top_row_controls, spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    talent_row_controls: list[ft.Control] = [
        create_mini_talent_tag("A", vm.talent_na),
        create_mini_talent_tag("E", vm.talent_e),
        create_mini_talent_tag("Q", vm.talent_q),
    ]
    talent_row = ft.Row(controls=talent_row_controls, spacing=5)

    weapon_info = f"{vm.weapon.display_name[:10]}  Lv.{vm.weapon.level}" if vm.weapon and vm.weapon.name else "未装备武器"
    weapon_row_controls: list[ft.Control] = [
        ft.Icon(ft.Icons.SHIELD, size=11, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
        ft.Text(
            weapon_info, 
            size=10, 
            color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE), 
            no_wrap=True, 
            overflow=ft.TextOverflow.ELLIPSIS, 
            expand=True
        )
    ]
    weapon_row = ft.Row(controls=weapon_row_controls, spacing=5)

    # 圣遗物摘要逻辑 (可以进一步移入 VM)
    artifact_row_controls: list[ft.Control] = [
        ft.Icon(ft.Icons.AUTO_AWESOME, size=11, color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
        ft.Text(
            vm.artifact_set_summary, 
            size=10, 
            color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE), 
            no_wrap=True, 
            overflow=ft.TextOverflow.ELLIPSIS, 
            expand=True
        )
    ]
    artifact_row = ft.Row(controls=artifact_row_controls, spacing=5)

    divider = ft.Container(
        height=1, 
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), 
        margin=ft.Margin.symmetric(vertical=2)
    )

    # 4. 组装容器
    stack_controls: list[ft.Control] = [
        # 背景渐变层
        ft.Container(
            expand=True, 
            border_radius=12,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                colors=[
                    ft.Colors.with_opacity(bg_opacity, elem_color),
                    ft.Colors.with_opacity(bg_opacity * 0.3, elem_color),
                ]
            )
        ),
        # 内容主体层
        ft.Container(
            content=ft.Column(
                controls=[top_row, divider, talent_row, weapon_row, artifact_row], 
                spacing=5, 
                alignment=ft.MainAxisAlignment.START
            ),
            padding=ft.Padding(11, 11, 11, 10), 
            expand=True,
        )
    ]

    return ft.Container(
        content=ft.Stack(controls=stack_controls),
        expand=True,
        border_radius=12,
        border=ft.Border.all(border_w, ft.Colors.with_opacity(border_alpha, elem_color)),
        shadow=[GenshinTheme.get_element_glow(vm.element, 0.55)] if is_selected else None,
        offset=ft.Offset(0.04, 0) if is_selected else ft.Offset(0, 0),
        on_click=lambda _: on_click(index) if on_click else None,
        animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
    )
