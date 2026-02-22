import flet as ft
import math
from ui.theme import GenshinTheme
from ui.reboot.components.stat_input import StatInputField
from ui.reboot.components.asset_grid import AssetGrid
from ui.reboot.components.spatial_radar import SpatialRadar
from ui.reboot.components.target_sidebar_slot import TargetSidebarSlot
from ui.state import AppState

class SceneView(ft.Container):
    """
    场景配置视图：采用原子化组件架构
    """
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
        self.state = self.app_state.strategic_state
        self.expand = True
        self.bgcolor = GenshinTheme.BACKGROUND
        self.padding = 0 
        
        self.sidebar_slots = []
        self.radar = None
        
        self._build_ui()

    def _build_ui(self):
        # 1. 顶部操作栏
        self.header = ft.Row([
            ft.Text("战场场景编排", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Row([])
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 2. 左侧目标侧边栏
        self.sidebar_slots = [
            TargetSidebarSlot(
                i, self.state.targets[i], 
                is_selected=(i == self.state.selected_target_index),
                on_click=self._handle_target_select,
                on_remove=self._handle_remove_target
            ) for i in range(len(self.state.targets))
        ]
        
        self.sidebar = ft.Column(
            self.sidebar_slots, 
            width=180, 
            expand=True, 
            spacing=10
        )
        if len(self.state.targets) < 5:
            self.sidebar.controls.append(self._build_add_target_button())

        # 3. 动态工作台内容
        self.workbench_content = ft.Column(
            controls=self._build_workbench_controls(),
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=30 
        )

        # 组装主布局
        self.main_layout = ft.Container(
            content=ft.Column([
                self.header,
                ft.Row([
                    ft.Container(content=self.sidebar, width=180),
                    ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.1, GenshinTheme.ON_SURFACE)),
                    self.workbench_content
                ], expand=True)
            ], spacing=10),
            padding=15,
            expand=True
        )
        self.content = self.main_layout

    def _build_workbench_controls(self):
        target = self.state.current_target
        target_id = target['id']
        pos = self.state.spatial_data['target_positions'].get(target_id, {"x": 0.0, "z": 0.0})
        dist = math.sqrt(pos['x']**2 + pos['z']**2)

        # --- A. 上半区：一体化概览面板 ---
        input_columns = ft.Column([
            ft.Text("目标定义与空间定位", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
            ft.Row([
                ft.TextField(
                    value=target['name'], label="怪物名称", dense=True, text_size=13,
                    expand=3, border_color=ft.Colors.WHITE_24, 
                    focused_border_color=ft.Colors.RED_400,
                    on_blur=lambda e: self._handle_target_name_change(e.control.value)
                ),
                ft.TextField(
                    value=str(target['level']), label="等级", dense=True, text_size=13,
                    width=100, border_color=ft.Colors.WHITE_24,
                    focused_border_color=ft.Colors.RED_400,
                    on_blur=lambda e: self._handle_target_stat_change("level", e.control.value)
                ),
            ], spacing=15),
            ft.Row([
                ft.TextField(
                    value=str(pos['x']), label="X 坐标 (左/右)", dense=True, text_size=13,
                    expand=1, border_color=ft.Colors.WHITE_24,
                    on_blur=lambda e: self._handle_pos_change("x", e.control.value)
                ),
                ft.TextField(
                    value=str(pos['z']), label="Z 坐标 (前/后)", dense=True, text_size=13,
                    expand=1, border_color=ft.Colors.WHITE_24,
                    on_blur=lambda e: self._handle_pos_change("z", e.control.value)
                ),
            ], spacing=15),
            ft.Row([
                ft.Chip(label=ft.Text("重置位置", size=10), on_click=lambda _: self._handle_reset_pos()),
                ft.Chip(label=ft.Text("标准抗性", size=10), on_click=lambda _: self._handle_reset_resists()),
                ft.Text(f"当前直线距离: {dist:.1f}m", size=11, italic=True, color=ft.Colors.PRIMARY)
            ], spacing=10)
        ], expand=True, spacing=15)

        # 空间雷达 (原子组件)
        self.radar = SpatialRadar(
            self.state.targets, 
            self.state.spatial_data['target_positions'], 
            self.state.selected_target_index
        )

        upper_panel = ft.Container(
            content=ft.Row([input_columns, self.radar], spacing=40, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.Padding(25, 20, 25, 20),
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            border_radius=15
        )

        # --- B. 下半区：抗性平铺录入 ---
        res = target['resists']
        res_keys = ["火", "水", "草", "雷", "风", "冰", "岩", "物理"]
        elem_map = {
            "火": "Pyro", "水": "Hydro", "草": "Dendro", "雷": "Electro",
            "风": "Anemo", "冰": "Cryo", "岩": "Geo", "物理": "Neutral"
        }
        elem_icons = {
            "火": ft.Icons.WHATSHOT, "水": ft.Icons.WATER_DROP, "草": ft.Icons.GRASS, 
            "雷": ft.Icons.FLASH_ON, "风": ft.Icons.AIR, "冰": ft.Icons.AC_UNIT, 
            "岩": ft.Icons.LANDSCAPE, "物理": ft.Icons.SHIELD
        }
        
        res_row = ft.Row(
            controls=[
                StatInputField(
                    label=k, 
                    value=res.get(k, "10"), 
                    suffix="%", 
                    width=140,
                    element=elem_map.get(k, "Neutral"),
                    icon=elem_icons.get(k),
                    on_change=lambda v, key=k: self._handle_res_change(key, v)
                ) for k in res_keys
            ],
            wrap=True, spacing=10, run_spacing=10
        )

        lower_section = ft.Column([
            ft.Text("抗性数值配置", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
            ft.Container(content=res_row, padding=ft.Padding(0, 10, 0, 10))
        ], spacing=10)

        return [upper_panel, lower_section, ft.Container(height=20)]

    def _build_add_target_button(self):
        return ft.Container(
            content=ft.Icon(ft.Icons.ADD, size=20, color=ft.Colors.WHITE_24),
            height=60, alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
            border_radius=12, border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
            on_click=lambda _: self._show_target_picker()
        )

    # --- 逻辑处理 ---
    def _handle_target_select(self, index):
        self.state.selected_target_index = index
        self._refresh_all()

    def _handle_remove_target(self, index):
        self.state.remove_target(index)
        self._refresh_all()

    def _handle_target_name_change(self, new_name):
        self.state.current_target['name'] = new_name
        self._refresh_sidebar()

    def _handle_target_stat_change(self, key, val):
        self.state.current_target[key] = val
        self._refresh_sidebar()

    def _handle_res_change(self, key, val):
        self.state.current_target['resists'][key] = val

    def _handle_pos_change(self, axis, val):
        try:
            target_id = self.state.current_target['id']
            self.state.spatial_data['target_positions'][target_id][axis] = float(val or 0)
            self._refresh_all()
        except: pass

    def _handle_reset_pos(self):
        target_id = self.state.current_target['id']
        self.state.spatial_data['target_positions'][target_id] = {"x": 0.0, "z": 5.0}
        self._refresh_all()

    def _handle_reset_resists(self):
        for k in self.state.current_target['resists']:
            self.state.current_target['resists'][k] = "10"
        self._refresh_all() 

    def _refresh_all(self):
        self.workbench_content.controls = self._build_workbench_controls()
        self._refresh_sidebar()
        try: self.update()
        except: pass

    def _refresh_sidebar(self):
        self.sidebar.controls = [
            TargetSidebarSlot(
                i, self.state.targets[i], 
                is_selected=(i == self.state.selected_target_index),
                on_click=self._handle_target_select,
                on_remove=self._handle_remove_target
            ) for i in range(len(self.state.targets))
        ]
        if len(self.state.targets) < 5:
            self.sidebar.controls.append(self._build_add_target_button())
        try: self.sidebar.update()
        except: pass

    def _show_target_picker(self):
        mock_monsters = []
        for name, info in self.app_state.target_map.items():
            mock_monsters.append({"id": name, "name": name, "rarity": 4})
            
        def on_monster_select(mid):
            self.state.add_target(mid)
            self.page.pop_dialog()
            self._refresh_all()
            
        picker_grid = AssetGrid(mock_monsters, on_select=on_monster_select, allow_filter_type=False, allow_filter_element=False)
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text("选择怪物实体"),
            content=ft.Container(picker_grid, width=500, height=400),
            bgcolor=GenshinTheme.SURFACE
        ))
