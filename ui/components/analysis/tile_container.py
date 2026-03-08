import flet as ft
from typing import Callable, Any, cast
from ui.components.analysis.base_widget import AnalysisTile

# --- Action Cluster Components ---

@ft.component
def ActionButton(
    icon: Any, 
    color: str = ft.Colors.WHITE_38, 
    tooltip: str = "", 
    on_click: Callable[..., Any] | None = None
):
    """微型操作按钮"""
    return ft.IconButton(
        icon=icon,
        icon_size=12,
        icon_color=color,
        tooltip=tooltip,
        width=24,
        height=24,
        on_click=on_click,
        style=ft.ButtonStyle(
            padding=0,
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
        )
    )

@ft.component
def TileContainer(
    tile: AnalysisTile, 
    on_close: Callable[[str], None], 
    on_maximize: Callable[[str], None], 
    is_maximized: bool = False, 
    key: str | None = None
):
    """
    [V4.5 Pro] 全新一代专业复盘磁贴容器。
    特点：1.5px 抗锯齿边框、色彩呼应渐变、声明式状态驱动。
    """
    # 1. 核心状态
    is_hovered, set_is_hovered = ft.use_state(False)

    # 2. 样式元数据
    # 根据磁贴定义的主题色进行呼应
    theme_color = getattr(tile, "theme_color", "#D3BC8E")  # 默认金
    gradient_top = getattr(tile, "gradient_top", "#2A2634")  # 默认深紫
    
    # 3. 动态属性计算
    border_style = ft.Border.all(
        1.5, 
        ft.Colors.with_opacity(0.6, theme_color) if is_hovered else ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
    )
    
    # 悬浮态背景亮度增强
    current_gradient = ft.LinearGradient(
        begin=ft.Alignment(0, -1),
        end=ft.Alignment(0, 1),
        colors=["#353042", "#25212B"] if is_hovered else [gradient_top, "#14111B"]
    )

    # 4. 标题栏构造
    iid = tile.instance_id or "UNKNOWN"
    
    header_left_controls: list[ft.Control] = [
        # 状态指示呼吸灯
        ft.Container(
            width=6,
            height=6, 
            bgcolor=theme_color, 
            border_radius=3,
            shadow=ft.BoxShadow(blur_radius=8, color=theme_color) if is_hovered else None,
            animate=200
        ),
        ft.Text(tile.title, size=11, weight=ft.FontWeight.W_700, color=ft.Colors.WHITE, opacity=0.9),
    ]

    header_right_controls: list[ft.Control] = [
        ActionButton(ft.Icons.SETTINGS_OUTLINED, tooltip="配置数据源"),
        ActionButton(
            ft.Icons.FULLSCREEN_EXIT_ROUNDED if is_maximized else ft.Icons.OPEN_IN_FULL_ROUNDED, 
            tooltip="退出全屏" if is_maximized else "聚焦复盘",
            on_click=lambda _: on_maximize(iid) if on_maximize and iid != "UNKNOWN" else None
        ),
        ActionButton(
            ft.Icons.CLOSE_ROUNDED, 
            color=ft.Colors.RED_400, 
            tooltip="移除磁贴",
            on_click=lambda _: on_close(iid) if on_close and iid != "UNKNOWN" else None
        ),
    ]

    header = ft.Row(
        controls=[
            ft.Row(controls=header_left_controls, spacing=8),
            # 悬浮操作集群 (Hover 显现)
            ft.Row(
                controls=header_right_controls, 
                spacing=4, 
                opacity=1.0 if is_hovered or is_maximized else 0, 
                animate_opacity=200
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # 5. 内容区包装
    tile_content = tile.render() if hasattr(tile, 'render') else cast(Any, tile)
    
    main_column_controls: list[ft.Control] = [
        header,
        ft.Container(content=tile_content, expand=True),
        # 统一页脚元数据
        ft.Row(
            controls=[
                ft.Text("LIVE_FEED", size=8, color=ft.Colors.WHITE_10, weight=ft.FontWeight.BOLD),
                ft.Text(f"ID_{iid[-4:].upper()}", size=8, color=ft.Colors.WHITE_10),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    ]

    return ft.GestureDetector(
        on_enter=lambda _: set_is_hovered(True),
        on_exit=lambda _: set_is_hovered(False),
        mouse_cursor=ft.MouseCursor.BASIC,
        content=ft.Container(
            key=key,
            padding=ft.Padding(16, 12, 16, 12),
            border_radius=14,
            border=border_style,
            gradient=current_gradient,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            shadow=[ft.BoxShadow(
                blur_radius=20,
                spread_radius=-10,
                color=ft.Colors.with_opacity(0.5 if is_hovered else 0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 8)
            )],
            content=ft.Column(controls=main_column_controls, spacing=5)
        )
    )
