import flet as ft
import asyncio
from ui.theme import GenshinTheme

class BaseAnalysisWidget(ft.Container):
    """
    分析组件基类 (V3.2 模块化架构)
    
    职责:
    1. 封装通用的卡片样式与标题栏。
    2. 提供标准的生命周期接口 (load_data, sync_frame)。
    3. 管理最大化、设置菜单及关闭逻辑。
    """
    def __init__(
        self, 
        view_id: str, 
        name: str, 
        icon: ft.Icons, 
        adapter, 
        col_span: int = 6, 
        height: int = 300,
        on_maximize=None,
        on_close=None
    ):
        # 核心属性
        self.view_id = view_id
        self.name = name
        self.icon = icon
        self.adapter = adapter
        self.col_span = col_span
        self.original_col = col_span
        self.original_height = height
        
        # 回调
        self.on_maximize_cb = on_maximize
        self.on_close_cb = on_close
        
        # 内部状态
        self.is_maximized = False
        self.current_frame = 0
        self.is_loading = False
        self.config = {} # 子类专用的局部配置上下文

        # UI 元素：标题与同步状态
        self.title_text = ft.Text(name, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self.subtitle_text = ft.Text("", size=10, opacity=0.5)
        
        # 精致的同步指示灯
        self.sync_dot = ft.Container(
            width=6, height=6, 
            border_radius=3, 
            bgcolor=ft.Colors.WHITE10,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
        )
        self.sync_label = ft.Text("READY", size=9, opacity=0.3, weight=ft.FontWeight.BOLD)
        
        # UI 元素：按钮组
        self.maximize_btn = ft.IconButton(
            icon=ft.Icons.ZOOM_IN_MAP_ROUNDED, 
            icon_size=14, 
            opacity=0.6,
            tooltip="最大化",
            on_click=self._handle_maximize_click
        )
        
        self.settings_menu = ft.PopupMenuButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            icon_size=14,
            opacity=0.6,
            items=[] 
        )

        # 核心内容容器
        self.body = ft.Container(expand=True)

        # 初始化 Container 样式 (玻璃拟态 + 阴影)
        super().__init__(
            col={"sm": 12, "md": 6, "xl": col_span},
            height=height,
            bgcolor="rgba(45, 45, 60, 0.4)",
            blur=ft.Blur(15, 15), # 磨砂玻璃
            border=ft.Border.all(1, "rgba(255,255,255,0.08)"),
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color="rgba(0,0,0,0.25)",
                offset=ft.Offset(0, 10)
            ),
            animate=ft.Animation(400, ft.AnimationCurve.DECELERATE),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS
        )

        self._build_layout()

    def _build_layout(self):
        """构建标准化的标题栏与内容区布局"""
        self.content = ft.Column([
            # 1. Header Section (精致化)
            ft.Container(
                content=ft.Row([
                    # Left: Icon + Title
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(self.icon, size=16, color=GenshinTheme.PRIMARY),
                            padding=ft.Padding(8, 8, 8, 8),
                            bgcolor="rgba(209, 162, 255, 0.1)",
                            border_radius=8
                        ),
                        ft.Column([
                            self.title_text,
                            self.subtitle_text
                        ], spacing=0, tight=True)
                    ], spacing=12),
                    
                    # Right: Sync Status + Tools
                    ft.Row([
                        ft.Row([
                            self.sync_dot,
                            self.sync_label
                        ], spacing=6),
                        ft.VerticalDivider(width=1, color="rgba(255,255,255,0.1)"),
                        self.maximize_btn,
                        self.settings_menu,
                        ft.IconButton(
                            icon=ft.Icons.CLOSE_ROUNDED, 
                            icon_size=16, 
                            opacity=0.6,
                            hover_color=ft.Colors.RED_400,
                            on_click=lambda _: self.on_close_cb(self) if self.on_close_cb else None
                        )
                    ], spacing=8)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.Padding(left=12, right=8, top=10, bottom=10),
                border=ft.Border.only(bottom=ft.BorderSide(1, "rgba(255,255,255,0.05)"))
            ),
            
            # 2. Body Section
            ft.Container(
                content=self.body,
                expand=True,
                padding=15
            )
        ], spacing=0)

    # --- 生命周期接口 (由子类重写) ---

    async def load_data(self):
        """
        [异步] 加载宏观全量数据。
        通常在组件创建、Session 切换或关键配置更改时调用。
        """
        pass

    async def sync_frame(self, frame_id: int):
        """[异步] 全局时间轴同步"""
        self.current_frame = frame_id
        # 激活同步指示灯
        self.sync_dot.bgcolor = ft.Colors.GREEN_400
        self.sync_dot.shadow = ft.BoxShadow(blur_radius=8, color="rgba(102, 255, 102, 0.4)")
        self.sync_label.value = f"LIVE F:{frame_id}"
        self.sync_label.opacity = 0.8
        self.sync_label.color = ft.Colors.GREEN_100
        
        try:
            self.update()
        except: pass

    def get_settings_items(self) -> list[ft.PopupMenuItem]:
        """
        [接口] 返回该组件特有的设置项。
        """
        return []

    # --- 内部逻辑控制 ---

    def _handle_maximize_click(self, e):
        """处理最大化按钮点击"""
        self.is_maximized = not self.is_maximized
        self.maximize_btn.icon = ft.Icons.ZOOM_OUT_MAP_ROUNDED if self.is_maximized else ft.Icons.ZOOM_IN_MAP_ROUNDED
        self.maximize_btn.tooltip = "还原" if self.is_maximized else "最大化"
        
        if self.on_maximize_cb:
            self.on_maximize_cb(self, self.is_maximized)
        
        try:
            self.update()
        except: pass

    def update_subtitle(self, text: str):
        """更新副标题 (通常用于展示当前观测对象)"""
        self.subtitle_text.value = text
        try:
            self.update()
        except: pass

    def refresh_settings_menu(self):
        """刷新设置菜单项"""
        self.settings_menu.items = self.get_settings_items()
        try:
            self.update()
        except: pass
