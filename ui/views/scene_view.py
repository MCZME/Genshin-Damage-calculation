import flet as ft
from ui.states.strategic_state import StrategicState
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter
from ui.components.scene.stat_input import StatInputField
from ui.components.common.asset_grid import AssetGrid
from ui.components.scene.spatial_radar import SpatialRadar
from ui.components.scene.target_sidebar_slot import TargetSidebarSlot
from ui.states.app_state import AppState

class SceneView:
    """
    场景配置视图 (MVVM V5.0)。
    通过 TargetViewModel 实现怪物属性与空间定位的深度聚合。
    """
    def __init__(self, state: AppState):
        self.app_state = state
        self.library_vm = state.library_vm

    @ft.component
    def build(self, state: StrategicState):
        # 1. 局部 UI 状态
        is_picker_open, set_is_picker_open = ft.use_state(False)

        # 2. 绑定核心 VM (直接从传入的 state 获取以激活 Flet 响应式)
        target_vms = state.target_vms
        active_target_vm = state.current_target_vm
        selected_index = state.selected_target_index

        # 3. 布局构建
        # 4.1 顶部操作栏
        header = ft.Row([
            ft.Text("战场场景编排", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 4.2 左侧侧边栏
        sidebar_controls = [
            TargetSidebarSlot(
                i, target_vms[i].model.raw_data, 
                is_selected=(i == selected_index),
                on_click=lambda idx: [setattr(state, "selected_target_index", idx), state.notify()],
                on_remove=lambda idx: state.remove_target(idx)
            ) for i in range(len(target_vms))
        ]
        
        # 处理添加按钮
        if len(target_vms) < 5:
            sidebar_controls.append(
                ft.Container(
                    content=ft.Icon(ft.Icons.ADD, size=20, color=ft.Colors.WHITE_24),
                    height=60, alignment=ft.Alignment.CENTER,
                    bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
                    border_radius=12, border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
                    on_click=lambda _: set_is_picker_open(True)
                )
            )
        
        sidebar = ft.Column(sidebar_controls, width=180, expand=True, spacing=10)

        # 4.3 中央工作台
        # 上半区：定位面板 (绑定到 active_target_vm)
        input_columns = ft.Column([
            ft.Text("目标定义与空间定位", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
            ft.Row([
                ft.TextField(
                    value=active_target_vm.name, label="怪物名称", dense=True, text_size=13,
                    expand=3, border_color=ft.Colors.WHITE_24, 
                    on_change=lambda e: active_target_vm.set_name(e.control.value)
                ),
                ft.TextField(
                    value=str(active_target_vm.level), label="等级", dense=True, text_size=13,
                    width=100, border_color=ft.Colors.WHITE_24,
                    on_change=lambda e: active_target_vm.set_level(int(e.control.value or 0))
                ),
            ], spacing=15),
            ft.Row([
                ft.TextField(
                    value=str(active_target_vm.x), label="X 坐标 (左/右)", dense=True, text_size=13,
                    expand=1, border_color=ft.Colors.WHITE_24,
                    on_change=lambda e: [active_target_vm.set_x(float(e.control.value or 0)), state.notify()]
                ),
                ft.TextField(
                    value=str(active_target_vm.z), label="Z 坐标 (前/后)", dense=True, text_size=13,
                    expand=1, border_color=ft.Colors.WHITE_24,
                    on_change=lambda e: [active_target_vm.set_z(float(e.control.value or 0)), state.notify()]
                ),
            ], spacing=15),
            ft.Row([
                ft.Chip(label=ft.Text("重置位置", size=10), on_click=lambda _: [active_target_vm.reset_position(), state.notify()]),
                ft.Text(f"当前距离: {UIFormatter.format_distance({'x': active_target_vm.x, 'z': active_target_vm.z})}", size=11, italic=True, color=ft.Colors.PRIMARY)
            ], spacing=10)
        ], expand=True, spacing=15)

        # 雷达图 (绑定到 target_vms)
        radar = SpatialRadar(target_vms, selected_index)

        upper_panel = ft.Container(
            content=ft.Row([input_columns, radar], spacing=40, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(25, 20, 25, 20),
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            border_radius=15
        )

        # 下半区：抗性录入 (核心修复：直接读取 VM 属性并手动触发 Parent Notify)
        res_keys = ["火", "水", "草", "雷", "风", "冰", "岩", "物理"]
        elem_map = {"火": "Pyro", "水": "Hydro", "草": "Dendro", "雷": "Electro", "风": "Anemo", "冰": "Cryo", "岩": "Geo", "物理": "Neutral"}
        
        # 实时获取抗性数据
        current_resists = active_target_vm.resistances

        res_row = ft.Row([
            StatInputField(
                label=k, value=str(current_resists.get(k, 10.0)), suffix="%", width=140,
                element=elem_map.get(k, "Neutral"), icon=UIFormatter.get_element_icon(elem_map.get(k, "Neutral")),
                on_change=lambda v, key=k: [active_target_vm.set_resistance(key, float(v or 0)), state.notify()]
            ) for k in res_keys
        ], wrap=True, spacing=10, run_spacing=10)

        lower_section = ft.Column([
            ft.Text("抗性数值配置", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
            ft.Container(content=res_row, padding=ft.Padding(0, 10, 0, 10))
        ], spacing=10)

        workbench_content = ft.Column([upper_panel, lower_section, ft.Container(height=20)], 
                                      expand=True, scroll=ft.ScrollMode.ADAPTIVE, spacing=30)

        # 5. 遮罩层构建
        overlay_content = None
        if is_picker_open:
            from ui.view_models.library_vm import AssetOption
            mock_monsters = [
                AssetOption(id=n, name=n, rarity=4, icon_path="", is_implemented=True) 
                for n in self.app_state.target_map.keys()
            ]
                
            def finish_monster_select(mid):
                state.add_target(mid)
                state.notify()
                set_is_picker_open(False)

            overlay_content = ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("选择怪物实体", size=18, weight=ft.FontWeight.W_800, color=GenshinTheme.PRIMARY),
                        ft.IconButton(ft.Icons.CLOSE, on_click=lambda _: set_is_picker_open(False))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    AssetGrid(mock_monsters, on_select=finish_monster_select, allow_filter_type=False, allow_filter_element=False)
                ], spacing=15),
                width=650, height=550, bgcolor=GenshinTheme.SURFACE, border_radius=16, padding=20
            )

        # 6. 最终组装
        return ft.Container(
            content=ft.Stack([
                ft.Column([
                    header,
                    ft.Row([
                        ft.Container(content=sidebar, width=180),
                        ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                        workbench_content
                    ], expand=True)
                ], spacing=10),
                ft.Container(
                    content=ft.Stack([
                        ft.Container(bgcolor="rgba(0,0,0,0.8)", on_click=lambda _: set_is_picker_open(False)),
                        ft.Container(content=overlay_content, alignment=ft.Alignment.CENTER),
                    ]),
                    visible=overlay_content is not None, expand=True
                )
            ]),
            padding=15, expand=True, bgcolor=GenshinTheme.BACKGROUND
        )
