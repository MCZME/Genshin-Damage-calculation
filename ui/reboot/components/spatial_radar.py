import flet as ft
import math

class SpatialRadar(ft.Container):
    """
    空间雷达可视化组件 (原子化重构版)。
    展示玩家(中心)与所有敌方实体的相对位置及欧氏距离。
    """
    def __init__(
        self, 
        targets: list, 
        target_positions: dict, 
        selected_index: int,
        size: int = 240,
        scale: int = 8 # 1m = 8px
    ):
        super().__init__()
        self.targets = targets
        self.target_positions = target_positions
        self.selected_index = selected_index
        self.radar_size = size
        self.radar_scale = scale
        
        self._build_ui()

    def _build_ui(self):
        # 1. 基础环辅助线
        rings = [self._create_ring(m, f"{m}m") for m in [5, 10, 15]]
        
        # 2. 坐标轴
        axes = [
            ft.Divider(height=1, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            ft.Text("X", size=9, color=ft.Colors.WHITE_12, offset=ft.Offset(7.5, 0)),
            ft.Text("Z", size=9, color=ft.Colors.WHITE_12, offset=ft.Offset(0, -7.5)),
        ]

        # 3. 玩家中心点
        player_dot = ft.Container(
            content=ft.Container(bgcolor=ft.Colors.BLUE_400, width=8, height=8, border_radius=4),
            width=16, height=16,
            alignment=ft.Alignment.CENTER,
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_200),
        )

        # 4. 目标点集
        target_dots = []
        guideline = ft.Container() # 距离引导线
        
        for i, t in enumerate(self.targets):
            t_id = t['id']
            pos = self.target_positions.get(t_id, {"x": 0.0, "z": 0.0})
            is_active = (i == self.selected_index)
            
            dot_size = 10 if is_active else 6
            off_row = (pos['x'] * self.radar_scale) / dot_size
            off_col = (-pos['z'] * self.radar_scale) / dot_size
            
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
            
            if is_active:
                dist = math.sqrt(pos['x']**2 + pos['z']**2)
                if dist > 0:
                    guideline = ft.Container(
                        width=dist * self.radar_scale, height=1,
                        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.RED_400),
                        rotate=math.atan2(pos['x'], pos['z']) - math.pi/2,
                        alignment=ft.Alignment.CENTER_LEFT,
                    )

        # 5. 组装 Stack
        self.content = ft.Stack([
            *rings,
            *axes,
            player_dot,
            guideline,
            *target_dots
        ], alignment=ft.Alignment.CENTER)
        
        self.width = self.radar_size
        self.height = self.radar_size
        self.bgcolor = ft.Colors.with_opacity(0.05, ft.Colors.BLACK)
        self.border_radius = self.radar_size / 2
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS

    def _create_ring(self, radius_m, label=None):
        px = radius_m * self.radar_scale
        return ft.Stack([
            ft.Container(
                width=px*2, height=px*2,
                border=ft.border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
                border_radius=px,
            ),
            ft.Text(label, size=8, color=ft.Colors.WHITE_12, offset=ft.Offset(0, -px/2)) if label else ft.Container()
        ], alignment=ft.Alignment.CENTER)

    def update_state(self, targets, target_positions, selected_index):
        """精准同步雷达状态"""
        self.targets = targets
        self.target_positions = target_positions
        self.selected_index = selected_index
        self._build_ui()
        try: self.update()
        except: pass
