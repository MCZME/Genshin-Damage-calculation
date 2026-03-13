"""
[V9.5 Pro V2] 角色实时面板仪表盘组件

正常态渲染逻辑 (2x2 Dashboard) - 集成自适应状态集群
[V9.6] 简化为纯 UI 组件，接收 ViewModel 实例
"""
import flet as ft

from ui.view_models.analysis.tile_vms.stats_vm import StatsViewModel
from ui.components.analysis.stats.status_capsule import StatusCapsuleWall
from ui.components.analysis.stats.status_indicator import CompactStatusBar
from ui.services.ui_formatter import UIFormatter


@ft.component
def StatsDashboard(vm: StatsViewModel):
    """[V9.6] 仪表盘渲染 - 纯 UI 组件

    接收由父组件传入的 ViewModel 实例，不再自行管理生命周期。
    """
    # 直接从 VM 获取数据
    theme_color = vm.theme_color
    element = vm.element
    char_name = vm.char_name
    frame_id = vm.frame_id

    # 获取动态数据
    shields = vm.shields

    # [V9.5] 获取带帧数信息的效果列表
    effects_with_frames = vm.active_effects_with_frames

    # 获取用户偏好
    stat_items = vm.get_display_stats()

    # [V9.5 Pro V2] 获取状态条选中状态（通过 VM 代理方法）
    status_selection = vm.get_status_bar_selection()
    status_indicators = vm.get_status_indicators(selection=status_selection)

    def create_stat_unit(key: str) -> ft.Control:
        total, bonus, _ = vm.calculate_stat(key)
        is_pct = any(x in key for x in ["率", "伤害", "充能", "加成", "效率"])
        fmt = ".1f" if is_pct else ".0f"
        suffix = "%" if is_pct else ""

        return ft.Column(
            controls=[
                ft.Text(key, size=9, color=ft.Colors.WHITE_54),
                ft.Text(f"{total:{fmt}}{suffix}", size=13, weight=ft.FontWeight.W_800),
            ],
            spacing=0,
            expand=1
        )

    # 构造网格
    grid_rows: list[ft.Control] = []
    for i in range(0, len(stat_items), 2):
        pair = stat_items[i:i + 2]
        row_controls: list[ft.Control] = [create_stat_unit(k) for k in pair]
        if len(row_controls) < 2:
            row_controls.append(ft.Container(expand=1))
        grid_rows.append(ft.Row(controls=row_controls, spacing=10))

    # [V9.5] 使用状态胶囊墙组件
    effect_capsules = StatusCapsuleWall(
        effects=effects_with_frames,
        max_visible=6,
        bgcolor=ft.Colors.BLACK_26
    )

    # 护盾标识
    shield_indicator = ft.Container()
    if shields:
        total_shield = vm.get_total_shield_hp()
        shield_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SHIELD_ROUNDED, size=10, color=ft.Colors.WHITE),
                ft.Text(f"{total_shield:.0f}", size=8, weight=ft.FontWeight.BOLD)
            ], spacing=2),
            bgcolor=ft.Colors.BLUE_GREY_700,
            padding=ft.Padding(left=4, right=4, top=1, bottom=1),
            border_radius=3
        )

    main_column_controls: list[ft.Control] = []

    # [V9.5 Pro V2] 顶部行：图标 + 名称 + 帧号
    top_row = ft.Row([
        ft.Row([
            ft.Icon(UIFormatter.get_element_icon(element), size=16, color=theme_color),
            ft.Text(char_name, size=13, weight=ft.FontWeight.BOLD),
        ], spacing=4),
        ft.Text(f"F_{frame_id}", size=9, color=ft.Colors.WHITE_10, font_family="Consolas")
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    main_column_controls.append(top_row)

    # [V9.5 Pro V2] 状态栏行：专用区域显示多个状态条
    has_visible_indicators = any(ind.get("visible", False) for ind in status_indicators)
    if has_visible_indicators:
        main_column_controls.append(
            ft.Container(
                content=CompactStatusBar(
                    indicators=status_indicators,
                    compact=True
                ),
                padding=ft.Padding(left=0, right=0, top=0, bottom=2)
            )
        )
    main_column_controls.append(ft.Divider(height=1, color=ft.Colors.WHITE_10))
    main_column_controls.append(ft.Column(controls=grid_rows, spacing=4, scroll=ft.ScrollMode.HIDDEN, expand=True))

    # [V9.5 Pro V2] 底部状态胶囊区域 - 始终显示
    bottom_row_controls: list[ft.Control] = []

    if effects_with_frames:
        bottom_row_controls.append(
            ft.Row([
                shield_indicator,
                effect_capsules,
            ], spacing=4, expand=True)
        )
    elif shields:
        bottom_row_controls.append(shield_indicator)

    if bottom_row_controls:
        main_column_controls.append(
            ft.Row(bottom_row_controls, alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )

    return ft.Column(
        controls=main_column_controls,
        expand=True,
        spacing=6
    )
