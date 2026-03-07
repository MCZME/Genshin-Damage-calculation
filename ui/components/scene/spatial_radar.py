import flet as ft
import math
from ui.view_models.scene.target_vm import TargetViewModel

@ft.component
def SpatialRadar(
    target_vms: list[TargetViewModel], 
    selected_index: int,
    size: int = 240,
    scale: int = 8 # 1m = 8px
):
    """
    声明式空间雷达可视化 (V5.0)。
    已重构为直接绑定 TargetViewModel，支持实时位置响应。
    """
    # --- 辅助工厂 ---
    def create_ring(radius_m, label=None):
        px = radius_m * scale
        return ft.Stack([
            ft.Container(
                width=px*2, height=px*2,
                border=ft.border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
                border_radius=px,
            ),
            ft.Text(label, size=8, color=ft.Colors.WHITE_12, offset=ft.Offset(0, -px/2)) if label else ft.Container()
        ], alignment=ft.Alignment.CENTER)

    # 1. 基础环与坐标轴
    rings = [create_ring(m, f"{m}m") for m in [5, 10, 15]]
    axes = [
        ft.Divider(height=1, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
        ft.VerticalDivider(width=1, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
        ft.Text("X", size=9, color=ft.Colors.WHITE_12, offset=ft.Offset(7.5, 0)),
        ft.Text("Z", size=9, color=ft.Colors.WHITE_12, offset=ft.Offset(0, -7.5)),
    ]

    # 2. 玩家中心点
    player_dot = ft.Container(
        content=ft.Container(bgcolor=ft.Colors.BLUE_400, width=8, height=8, border_radius=4),
        width=16, height=16, alignment=ft.Alignment.CENTER, border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE_200),
    )

    # 3. 目标点集
    target_dots = []
    guideline = ft.Container()
    
    for i, vm in enumerate(target_vms):
        # 核心：直接读取 VM 属性，建立 Flet 追踪链路
        pos_x = vm.x
        pos_z = vm.z
        is_active = (i == selected_index)
        
        dot_size = 10 if is_active else 6
        # 防止 dot_size 为 0 的计算
        off_row = (pos_x * scale) / dot_size if dot_size != 0 else 0
        off_col = (-pos_z * scale) / dot_size if dot_size != 0 else 0
        
        target_dots.append(
            ft.Container(
                bgcolor=ft.Colors.RED_400 if is_active else ft.Colors.with_opacity(0.3, ft.Colors.RED_900),
                width=dot_size, height=dot_size, border_radius=dot_size / 2,
                offset=ft.Offset(off_row, off_col),
                animate_offset=ft.Animation(300, ft.AnimationCurve.DECELERATE),
                tooltip=f"目标 {i+1}: {vm.name} ({pos_x:.1f}, {pos_z:.1f})",
                shadow=ft.BoxShadow(spread_radius=1, blur_radius=10, color=ft.Colors.with_opacity(0.4, ft.Colors.RED_400)) if is_active else None
            )
        )
        
        if is_active:
            dist = math.sqrt(pos_x**2 + pos_z**2)
            if dist > 0:
                guideline = ft.Container(
                    width=dist * scale, height=1,
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.RED_400),
                    rotate=math.atan2(pos_x, pos_z) - math.pi/2,
                    alignment=ft.Alignment.CENTER_LEFT,
                )

    # 4. 组装容器
    return ft.Container(
        content=ft.Stack([
            *rings, *axes, player_dot, guideline, *target_dots
        ], alignment=ft.Alignment.CENTER),
        width=size, height=size,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
        border_radius=size / 2,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS
    )
