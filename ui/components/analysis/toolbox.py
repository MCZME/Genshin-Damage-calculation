import flet as ft
from ui.theme import GenshinTheme

@ft.component
def ToolboxItem(label: str, icon: str, tid: str, is_expanded: bool, count: int, on_click):
    """单项工具箱按钮函数组件"""
    is_hover, set_is_hover = ft.use_state(False)
    is_active = count > 0

    # 状态颜色逻辑
    bg_color = "rgba(209, 162, 255, 0.12)" if is_active else ("rgba(255, 255, 255, 0.05)" if is_hover else "transparent")
    icon_color = GenshinTheme.PRIMARY if is_active else ft.Colors.WHITE_70
    text_color = ft.Colors.WHITE if is_active else ft.Colors.WHITE_70

    badge = None
    if count > 0:
        badge = ft.Container(
            content=ft.Text(str(count), size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            bgcolor=GenshinTheme.PRIMARY,
            padding=ft.Padding.symmetric(horizontal=4, vertical=1),
            border_radius=10,
            right=8, top=8
        )

    # 构造堆栈内容
    stack_controls = [
        ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=20, color=icon_color),
                    width=48, 
                    alignment=ft.Alignment.CENTER
                ),
                ft.Container(
                    content=ft.Text(label, size=13, weight=ft.FontWeight.W_500, no_wrap=True, color=text_color),
                    opacity=1 if is_expanded else 0,
                    animate_opacity=300,
                    margin=ft.margin.only(left=15)
                )
            ], spacing=0, tight=True),
            height=48,
            border_radius=12,
            bgcolor=bg_color,
            on_click=lambda _: on_click(tid) if on_click else None,
            on_hover=lambda e: set_is_hover(e.data == "true"),
            animate=ft.Animation(200, ft.AnimationCurve.DECELERATE),
        )
    ]
    
    if badge and not is_expanded:
        stack_controls.append(badge)

    return ft.Stack(stack_controls)

@ft.component
def AnalysisToolbox(active_counts: dict[str, int], on_tile_action=None):
    """
    分析工具箱 (V4.9 声明式函数组件版)。
    使用 use_state 确保折叠状态在重绘间持久化。
    """
    is_expanded, set_is_expanded = ft.use_state(False)

    # 磁贴配置
    items_config = [
        ("历史记录", ft.Icons.HISTORY_ROUNDED, "history"),
        ("角色面板", ft.Icons.PERSON_SEARCH_ROUNDED, "stats"),
        ("伤害分布", ft.Icons.QUERY_STATS_ROUNDED, "damage_dist"),
        ("DPS 曲线", ft.Icons.AUTO_GRAPH_ROUNDED, "dps"),
        ("全局战报", ft.Icons.DASHBOARD_ROUNDED, "summary"),
    ]

    def toggle_collapse(_):
        set_is_expanded(not is_expanded)

    header = ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.IconButton(
                    ft.Icons.MENU_OPEN_ROUNDED if is_expanded else ft.Icons.MENU_ROUNDED,
                    icon_size=20, on_click=toggle_collapse, style=ft.ButtonStyle(shape=ft.CircleBorder())
                ), width=48, alignment=ft.Alignment.CENTER
            ),
            ft.Container(
                content=ft.Text("MENU", size=14, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE, style=ft.TextStyle(letter_spacing=2)),
                opacity=1 if is_expanded else 0, animate_opacity=300, margin=ft.margin.only(left=15)
            )
        ], spacing=0, tight=True),
        height=60, padding=ft.Padding.only(left=12, top=0, right=0, bottom=0)
    )

    menu_items = [
        ToolboxItem(
            label=label, icon=icon, tid=tid, 
            is_expanded=is_expanded, count=active_counts.get(tid, 0), 
            on_click=on_tile_action
        )
        for label, icon, tid in items_config
    ]

    footer_items = [
        ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
        ToolboxItem(
            label="排轴预设", icon=ft.Icons.AUTO_AWESOME_MOTION_ROUNDED, tid="preset_rotation", 
            is_expanded=is_expanded, count=0, on_click=on_tile_action
        ),
        ToolboxItem(
            label="设置", icon=ft.Icons.SETTINGS_ROUNDED, tid="settings", 
            is_expanded=is_expanded, count=0, on_click=on_tile_action
        ),
    ]

    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(
                content=ft.Column(menu_items, spacing=8, scroll=ft.ScrollMode.HIDDEN), 
                expand=True, 
                padding=ft.Padding.only(left=12, top=0, right=12, bottom=0)
            ),
            ft.Container(
                content=ft.Column(footer_items, spacing=5), 
                padding=ft.Padding.all(12)
            )
        ], spacing=0),
        width=220 if is_expanded else 72,
        bgcolor="#1A1625",
        border=ft.border.only(right=ft.border.BorderSide(1, "rgba(255, 255, 255, 0.05)")),
        animate=ft.Animation(400, ft.AnimationCurve.EASE_OUT_QUINT)
    )
