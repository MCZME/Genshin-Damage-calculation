import flet as ft
import math
from ui.theme import GenshinTheme
from ui.reboot.state import StrategicState
from ui.reboot.components.stat_input import StatInputField
from ui.reboot.components.asset_grid import AssetGrid
from ui.state import AppState

class SceneView(ft.Container):
    """
    场景配置视图 - 纯数值录入版 (修复显示问题)。
    确保所有输入框具有明确的宽度和扩展性，防止 UI 塌缩。
    """
    def __init__(self, app_state: AppState):
        super().__init__()
        self.app_state = app_state
        self.state = self.app_state.strategic_state
        self.expand = True
        self.bgcolor = GenshinTheme.BACKGROUND
        self.padding = 0 
        self._build_ui()

    def _build_ui(self):
        # 1. 顶部操作栏
        self.header = ft.Row([
            ft.Text("战场场景编排", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Row([])

        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 2. 左侧目标侧边栏
        self.sidebar_slots = [self._build_target_slot(i) for i in range(len(self.state.targets))]
        if len(self.state.targets) < 5:
            self.sidebar_slots.append(self._build_add_target_button())

        self.sidebar = ft.Column(self.sidebar_slots, width=180, expand=True, spacing=10)

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
        
        # 左侧输入区域
        input_columns = ft.Column([
            ft.Text("目标定义与空间定位", size=16, weight=ft.FontWeight.BOLD, opacity=0.8),
            # 第一行：名称 + 等级
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
            # 第二行：坐标 X + 坐标 Z
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
            # 第三行：快捷操作
            ft.Row([
                ft.Chip(label=ft.Text("重置位置", size=10), on_click=lambda _: self._handle_reset_pos()),
                ft.Chip(label=ft.Text("标准抗性", size=10), on_click=lambda _: self._handle_reset_resists()),
                ft.Text(f"当前直线距离: {dist:.1f}m", size=11, italic=True, color=ft.Colors.PRIMARY)
            ], spacing=10)
        ], expand=True, spacing=15)

        # 右侧战术雷达增强版
        RADAR_SIZE = 240
        SCALE = 8 # 1m = 8px
        
        def create_ring(radius_m, label=None):
            px = radius_m * SCALE 
            return ft.Stack([
                ft.Container(
                    width=px*2, height=px*2,

                    border=ft.border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
                    border_radius=px,
                ),
                ft.Text(label, size=8, color=ft.Colors.WHITE_12, offset=ft.Offset(0, -px/2)) if label else ft.Container()
            ], alignment=ft.Alignment.CENTER)

        target_dots = []
        for i, t in enumerate(self.state.targets):
            t_id = t['id']
            t_pos = self.state.spatial_data['target_positions'].get(t_id, {"x": 0.0, "z": 0.0})
            is_active = (i == self.state.selected_target_index)
            
            dot_size = 10 if is_active else 6
            # 计算 Offset：位移像素 / 控件尺寸
            # x_px = x * SCALE
            # offset_x = x_px / dot_size
            off_row = (t_pos['x'] * SCALE) / dot_size
            off_col = (-t_pos['z'] * SCALE) / dot_size
            
            target_dots.append(
                ft.Container(
                    bgcolor=ft.Colors.RED_400 if is_active else ft.Colors.with_opacity(0.3, ft.Colors.RED_900),
                    width=dot_size, height=dot_size,
                    border_radius=dot_size / 2,
                    offset=ft.Offset(off_row, off_col),
                    animate_offset=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                    tooltip=f"目标 {i+1}: {t['name']}",
                    shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.with_opacity(0.4, ft.Colors.RED_400)) if is_active else None
                )
            )


        # 玩家中心呼吸灯
        player_dot = ft.Container(
            content=ft.Container(bgcolor=ft.Colors.BLUE_400, width=8, height=8, border_radius=4),
            width=16, height=16,
            alignment=ft.Alignment.CENTER,
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_200),
            animate_scale=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
            # 这里可以用一个简单的 scale 动画模拟呼吸，但在静态构建中通过初始值设定
        )

        radar_view = ft.Container(
            content=ft.Stack([
                create_ring(5, "5m"),
                create_ring(10, "10m"),
                create_ring(15, "15m"),
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
                ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
                # X/Z 轴标注
                ft.Text("X", size=9, color=ft.Colors.WHITE_12, offset=ft.Offset(7.5, 0)),
                ft.Text("Z", size=9, color=ft.Colors.WHITE_12, offset=ft.Offset(0, -7.5)),
                player_dot,
                # 距离引导线 (仅显示当前选中目标)
                ft.Container(
                    width=dist * SCALE, height=1,
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.RED_400),
                    rotate=math.atan2(pos['x'], pos['z']) - math.pi/2,
                    alignment=ft.Alignment.CENTER_LEFT,
                    offset=ft.Offset(0, 0), # 锚点在中心
                ) if dist > 0 else ft.Container(),
                *target_dots
            ], alignment=ft.Alignment.CENTER),
            width=RADAR_SIZE, height=RADAR_SIZE,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            border_radius=RADAR_SIZE / 2, # 圆形雷达
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),

            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        upper_panel = ft.Container(
            content=ft.Row([input_columns, radar_view], spacing=40, vertical_alignment=ft.CrossAxisAlignment.CENTER),
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
        # 元素图标映射
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
                    icon=elem_icons.get(k), # 注入图标
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

    def _build_target_slot(self, index: int):
        target = self.state.targets[index]
        is_selected = (index == self.state.selected_target_index)
        theme_color = ft.Colors.RED_400 if is_selected else ft.Colors.RED_900
        
        bg_opacity = 0.28 if is_selected else 0.10
        bg_gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
            colors=[
                ft.Colors.with_opacity(bg_opacity, theme_color), 
                ft.Colors.with_opacity(bg_opacity * 0.3, theme_color)
            ]
        )

        avatar = ft.Container(
            content=ft.Text(str(index+1), size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
            width=36, height=36, bgcolor=ft.Colors.with_opacity(0.3, theme_color),
            border_radius=18, alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.6 if is_selected else 0.25, theme_color))
        )

        name_col = ft.Column([
            ft.Text(target['name'], size=13, weight=ft.FontWeight.W_900 if is_selected else ft.FontWeight.BOLD),
            ft.Text(f"Lv.{target['level']}", size=10, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
        ], spacing=1, expand=True)

        remove_btn = ft.Container(
            content=ft.Icon(ft.Icons.CLOSE, size=11, color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
            width=22, height=22, border_radius=11, alignment=ft.Alignment.CENTER,
            on_click=lambda _: self._handle_remove_target(index),
        ) if len(self.state.targets) > 1 else ft.Container()
        remove_btn.mouse_cursor = ft.MouseCursor.CLICK

        return ft.Container(
            content=ft.Stack([
                ft.Container(expand=True, gradient=bg_gradient, border_radius=12),
                ft.Container(
                    content=ft.Row([avatar, name_col, remove_btn], spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.Padding(11, 11, 11, 11)
                )
            ]),
            height=60, border_radius=12,
            border=ft.Border.all(2 if is_selected else 1, ft.Colors.with_opacity(0.65 if is_selected else 0.12, theme_color)),
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.with_opacity(0.5, theme_color)) if is_selected else None,
            on_click=lambda _: self._handle_target_select(index),
            offset=ft.Offset(0.04, 0) if is_selected else ft.Offset(0, 0),
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK),
        )


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
            self._refresh_all() # 坐标变动需要刷新雷达动点
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
        self.update()

    def _refresh_sidebar(self):
        self.sidebar.controls = [self._build_target_slot(i) for i in range(len(self.state.targets))]
        if len(self.state.targets) < 5:
            self.sidebar.controls.append(self._build_add_target_button())
        try: self.sidebar.update()
        except: pass

    def _show_target_picker(self):
        mock_monsters = []
        for name, info in self.app_state.target_map.items():
            mock_monsters.append({
                "id": name,
                "name": name,
                "rarity": 4 # 默认显示 4 星紫色底蕴
            })
            
        def on_monster_select(mid):
            selected_m = next(m for m in mock_monsters if m['id'] == mid)
            self.state.add_target(selected_m['name'])
            self.page.pop_dialog()
            self._refresh_all()
        picker_grid = AssetGrid(
            mock_monsters, 
            on_select=on_monster_select,
            allow_filter_type=False,
            allow_filter_element=False
        )
        self.page.show_dialog(ft.AlertDialog(
            title=ft.Text("选择怪物实体"),
            content=ft.Container(picker_grid, width=500, height=400),
            bgcolor=GenshinTheme.SURFACE
        ))
