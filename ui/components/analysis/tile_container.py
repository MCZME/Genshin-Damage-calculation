import flet as ft
from ui.theme import GenshinTheme
from ui.components.analysis.base_widget import AnalysisTile

class TileContainer(ft.Container):
    """
    通用磁贴包装器 (V6.0 艺术巅峰版)。
    采用“嵌套收缩”算法实现的金属边框，复刻《原神》五星品质质感。
    """
    def __init__(
        self, 
        tile: AnalysisTile, 
        on_close=None, 
        on_maximize=None,
        is_maximized: bool = False
    ):
        super().__init__()
        self.tile = tile
        self.on_close_callback = on_close
        self.on_maximize_callback = on_maximize
        self.is_maximized = is_maximized
        
        # 磁贴属性透传
        self.expand = self.tile.expand
        
        # 1. 外层容器：模拟“金属外壳”
        self.gradient = ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=[
                GenshinTheme.GOLD_LIGHT if not is_maximized else ft.Colors.with_opacity(0.1, ft.Colors.WHITE), 
                GenshinTheme.GOLD_DARK if not is_maximized else ft.Colors.with_opacity(0.05, ft.Colors.WHITE), 
                "#2A2435"
            ]
        )
        self.border_radius = ft.BorderRadius.only(top_left=34, bottom_right=34, top_right=8, bottom_left=8)
        self.padding = 2 # 边框厚度
        self.animate = ft.Animation(300, ft.AnimationCurve.DECELERATE)
        self.on_hover = self._handle_hover
        
        self._build_ui()

    def _build_ui(self):
        # 核心图标与样式引用
        self.max_icon = ft.Icon(
            ft.Icons.FULLSCREEN_EXIT_ROUNDED if self.is_maximized else ft.Icons.FULLSCREEN_ROUNDED, 
            size=16, 
            color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE)
        )

        # 2. 内层容器内容：核心暗紫色底色
        # 顶部光晕氛围层
        glow_layer = ft.Container(
            height=100,
            top=0, left=0, right=0,
            gradient=ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=[ft.Colors.with_opacity(0.15, GenshinTheme.GOLD_DARK), ft.Colors.TRANSPARENT]
            ),
        )
        
        # 背景暗纹层
        pattern_layer = ft.Container(
            content=ft.Icon(ft.Icons.AUTO_AWESOME, size=180, color=ft.Colors.with_opacity(0.01, ft.Colors.WHITE)),
            right=-50, bottom=-50
        )

        # 工具栏构建
        toolbar = ft.Row([
            self._build_tool_btn(ft.Icons.SETTINGS_ROUNDED, lambda _: self.tile.on_config_toggle()),
            ft.IconButton(
                icon=self.max_icon,
                on_click=lambda _: self.on_maximize_callback(self) if self.on_maximize_callback else None,
                style=ft.ButtonStyle(padding=0)
            ),
            self._build_tool_btn(ft.Icons.CLOSE_ROUNDED, 
                lambda _: self.on_close_callback(self) if self.on_close_callback else None,
                color=ft.Colors.RED_ACCENT_200
            ),
        ], spacing=2)

        # 头部标题区
        header_title = ft.Row([
            ft.Icon(self.tile.icon, size=16, color=GenshinTheme.GOLD_DARK),
            ft.Container(
                content=ft.Text(
                    self.tile.title, 
                    size=12, 
                    weight=ft.FontWeight.W_800, 
                    color=GenshinTheme.GOLD_DARK, 
                    style=ft.TextStyle(letter_spacing=1.2)
                ),
                padding=ft.Padding(0, 2, 0, 0)
            ),
        ], spacing=10)

        # 头部整体容器
        header = ft.Container(
            padding=ft.Padding(25, 15, 20, 12),
            border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE))),
            content=ft.Row([header_title, toolbar], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        )

        # 内容区 (保留引用供外部切换)
        self.content_area = ft.Container(
            content=self.tile,
            padding=ft.Padding(25, 20, 25, 25),
            expand=True if self.tile.expand else None
        )

        # 组装主体布局
        main_layout = ft.Column([
            header,
            self.content_area
        ], spacing=0, expand=True if self.tile.expand else None)

        # 最终内层 Container 包装
        self.content = ft.Container(
            bgcolor="#1A1625",
            border_radius=ft.BorderRadius.only(top_left=32, bottom_right=32, top_right=6, bottom_left=6),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            expand=True,
            content=ft.Stack([
                glow_layer,
                pattern_layer,
                main_layout
            ])
        )

    def _build_tool_btn(self, icon, on_click, color=ft.Colors.WHITE70):
        return ft.IconButton(
            icon=ft.Icon(icon, size=16, color=color),
            on_click=on_click,
            style=ft.ButtonStyle(
                shape=ft.CircleBorder(),
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                padding=0
            )
        )

    def _handle_hover(self, e):
        is_hover = e.data == "true"
        # 悬停时：外边框金色变亮，产生“高光流转”感
        self.gradient = ft.LinearGradient(
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
            colors=[
                ft.Colors.with_opacity(0.8, GenshinTheme.GOLD_LIGHT) if is_hover else GenshinTheme.GOLD_LIGHT,
                ft.Colors.with_opacity(0.6, GenshinTheme.GOLD_DARK) if is_hover else GenshinTheme.GOLD_DARK,
                "#352E45" if is_hover else "#2A2435"
            ]
        )
        try:
            self.update()
        except:
            pass

    def set_maximized(self, is_max: bool):
        self.is_maximized = is_max
        try:
            self.max_icon.name = (
                ft.Icons.FULLSCREEN_EXIT_ROUNDED if is_max else ft.Icons.FULLSCREEN_ROUNDED
            )
            # 最大化时，边框变淡以减少视觉负担
            self.gradient = ft.LinearGradient(
                begin=ft.Alignment(0, -1),
                end=ft.Alignment(0, 1),
                colors=[
                    ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if is_max else GenshinTheme.GOLD_LIGHT,
                    ft.Colors.with_opacity(0.05, ft.Colors.WHITE) if is_max else GenshinTheme.GOLD_DARK,
                    "#2A2435"
                ]
            )
            self.update()
        except: 
            pass
