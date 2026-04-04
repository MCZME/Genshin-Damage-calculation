"""场景配置视图。"""

from __future__ import annotations

import flet as ft
from typing import TYPE_CHECKING, cast

from ui.states.scene_state import SceneState
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter
from ui.components.scene.stat_input import StatInputField
from ui.components.common.asset_grid import AssetGrid
from ui.components.scene.spatial_radar import SpatialRadar
from ui.components.scene.target_sidebar_slot import TargetSidebarSlot
from ui.components.scene.rules_editor import RulesEditor

if TYPE_CHECKING:
    from ui.states.app_state import AppState
    from ui.services.persistence_manager import PersistenceManager


class SceneView:
    """
    场景配置视图 (MVVM V5.0)。

    通过 SceneState 管理目标实体与规则配置。
    """

    def __init__(self, state: AppState, persistence: PersistenceManager) -> None:
        self.app_state = state
        self.persistence = persistence
        self.library_vm = state.library_vm

    @ft.component
    def build(self, scene_state: SceneState):
        # 1. 局部 UI 状态
        is_picker_open, set_is_picker_open = ft.use_state(False)

        # 2. 绑定核心 VM
        target_vms = scene_state.target_vms
        active_target_vm = scene_state.current_target_vm
        selected_index = scene_state.selected_target_index

        # 3. 辅助处理器
        def handle_target_select(idx: int) -> None:
            scene_state.select_target(idx)

        def handle_pos_change(axis: str, value: str) -> None:
            try:
                num_val = float(value or 0)
                if axis == "x":
                    active_target_vm.set_x(num_val)
                else:
                    active_target_vm.set_z(num_val)
                scene_state.notify_update()
            except ValueError:
                pass

        def handle_resistance_change(key: str, value: str) -> None:
            try:
                active_target_vm.set_resistance(key, float(value or 0))
                scene_state.notify_update()
            except ValueError:
                pass

        # 4. 布局构建
        # 4.1 顶部操作栏
        header = ft.Row(
            controls=[
                ft.Text("战场场景编排", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # 4.2 左侧侧边栏
        sidebar_items: list[ft.Control] = [
            TargetSidebarSlot(
                i, target_vms[i].model.raw_data,
                is_selected=(i == selected_index),
                on_click=handle_target_select,
                on_remove=lambda idx: scene_state.remove_target(idx)
            ) for i in range(len(target_vms))
        ]

        # 处理添加按钮
        if len(target_vms) < 5:
            sidebar_items.append(
                ft.Container(
                    content=ft.Icon(ft.Icons.ADD, size=20, color=ft.Colors.WHITE_24),
                    height=60,
                    alignment=ft.Alignment.CENTER,
                    bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                    border_radius=12,
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
                    on_click=lambda _: set_is_picker_open(True)
                )
            )

        sidebar = ft.Column(controls=sidebar_items, width=180, expand=True, spacing=10)

        # 4.3 中央工作台
        # 上半区：定位面板
        input_columns_controls: list[ft.Control] = [
            ft.Text("目标定义与空间定位", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
            ft.Row(
                controls=[
                    ft.TextField(
                        value=active_target_vm.name, label="怪物名称", dense=True, text_size=13,
                        expand=3, border_color=ft.Colors.WHITE_24,
                        on_change=lambda e: active_target_vm.set_name(e.control.value or "")
                    ),
                    ft.TextField(
                        value=str(active_target_vm.defense), label="防御力", dense=True, text_size=13,
                        expand=2, border_color=ft.Colors.WHITE_24,
                        on_change=lambda e: active_target_vm.set_defense(int(e.control.value or 0))
                    ),
                    ft.TextField(
                        value=str(active_target_vm.level), label="等级", dense=True, text_size=13,
                        expand=2, border_color=ft.Colors.WHITE_24,
                        on_change=lambda e: active_target_vm.set_level(int(e.control.value or 0))
                    ),
                ],
                spacing=15
            ),
            ft.Row(
                controls=[
                    ft.TextField(
                        value=str(active_target_vm.x), label="X 坐标 (左/右)", dense=True, text_size=13,
                        expand=1, border_color=ft.Colors.WHITE_24,
                        on_change=lambda e: handle_pos_change("x", e.control.value or "")
                    ),
                    ft.TextField(
                        value=str(active_target_vm.z), label="Z 坐标 (前/后)", dense=True, text_size=13,
                        expand=1, border_color=ft.Colors.WHITE_24,
                        on_change=lambda e: handle_pos_change("z", e.control.value or "")
                    ),
                ],
                spacing=15
            ),
            ft.Row(
                controls=[
                    ft.Chip(
                        label=ft.Text("重置位置", size=10),
                        on_click=lambda _: [active_target_vm.reset_position(), scene_state.notify_update()]  # type: ignore[func-returns-value]
                    ),
                    ft.Text(
                        f"当前距离: {UIFormatter.format_distance({'x': active_target_vm.x, 'z': active_target_vm.z})}",
                        size=11,
                        italic=True,
                        color=ft.Colors.PRIMARY
                    )
                ],
                spacing=10
            )
        ]
        input_columns = ft.Column(controls=input_columns_controls, expand=True, spacing=15)

        # 雷达图
        radar = SpatialRadar(target_vms, selected_index)

        upper_panel = ft.Container(
            content=ft.Row(
                controls=[input_columns, radar],
                spacing=40,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.Padding(25, 20, 25, 20),
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            border_radius=15
        )

        # 下半区：抗性录入
        res_keys = ["火", "水", "草", "雷", "风", "冰", "岩", "物理"]
        elem_map = {
            "火": "Pyro", "水": "Hydro", "草": "Dendro", "雷": "Electro",
            "风": "Anemo", "冰": "Cryo", "岩": "Geo", "物理": "Neutral"
        }

        current_resists = active_target_vm.resistances

        res_controls = cast(list[ft.Control], [
            StatInputField(
                label=k, value=str(current_resists.get(k, 10.0)), suffix="%", width=140,
                element=elem_map.get(k, "Neutral"), icon=UIFormatter.get_element_icon(elem_map.get(k, "Neutral")),
                on_select=lambda v, key=k: handle_resistance_change(key, v)  # type: ignore[misc]
            ) for k in res_keys
        ])
        res_row = ft.Row(controls=res_controls, wrap=True, spacing=10, run_spacing=10)

        lower_section = ft.Column(
            controls=[
                ft.Text("抗性数值配置", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
                ft.Container(content=res_row, padding=ft.Padding(0, 10, 0, 10))
            ],
            spacing=10
        )

        # 上半部分：目标配置区域
        target_config_section = ft.Column(
            controls=[
                upper_panel,
                lower_section,
            ],
            spacing=30,
            expand=2,
        )

        # 下半部分：规则配置区域
        rules_config_section = ft.Container(
            content=RulesEditor(scene_state.rules_vm, self.persistence),
            expand=1,
        )

        # 整个工作台（上下分割）
        workbench_content = ft.Column(
            controls=[
                target_config_section,
                rules_config_section,
            ],
            expand=True,
            spacing=15,
        )

        # 5. 遮罩层构建
        overlay_content: ft.Control | None = None
        if is_picker_open:
            from ui.view_models.library_vm import AssetOption
            mock_monsters = [
                AssetOption(id=n, name=n, rarity=4, icon_path="", is_implemented=True)
                for n in self.app_state.target_map.keys()
            ]

            def finish_monster_select(mid: str) -> None:
                scene_state.add_target(mid)
                set_is_picker_open(False)

            overlay_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("选择怪物实体", size=18, weight=ft.FontWeight.W_800, color=GenshinTheme.PRIMARY),
                                ft.IconButton(ft.Icons.CLOSE, on_click=lambda _: set_is_picker_open(False))
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        AssetGrid(mock_monsters, on_select=finish_monster_select, allow_filter_type=False, allow_filter_element=False)
                    ],
                    spacing=15
                ),
                width=650, height=550, bgcolor=GenshinTheme.SURFACE, border_radius=16, padding=20
            )

        # 6. 最终组装
        main_layout_controls: list[ft.Control] = [
            header,
            ft.Row(
                controls=[
                    ft.Container(content=sidebar, width=180),
                    ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                    workbench_content
                ],
                expand=True
            )
        ]

        return ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Column(controls=main_layout_controls, spacing=10),
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                ft.Container(bgcolor="rgba(0,0,0,0.8)", on_click=lambda _: set_is_picker_open(False)),
                                ft.Container(content=overlay_content, alignment=ft.Alignment.CENTER),
                            ]
                        ),
                        visible=overlay_content is not None,
                        expand=True
                    )
                ]
            ),
            padding=15,
            expand=True,
            bgcolor=GenshinTheme.BACKGROUND
        )
