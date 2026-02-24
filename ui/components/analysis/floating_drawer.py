import flet as ft
from typing import Optional
from ui.theme import GenshinTheme

class FloatingDrawer(ft.Container):
    """
    纯悬浮详情容器。
    作为 Overlay 存在，不参与网格布局，支持从右侧滑入并带强毛玻璃效果。
    """
    def __init__(self, width: float = 400):
        super().__init__()
        self.drawer_width = width
        self.is_pinned = False
        
        # 核心引用
        self.pin_btn = None
        
        # 初始定位在屏幕右侧外部
        self.width = self.drawer_width
        self.right = -self.drawer_width
        self.top = 20
        self.bottom = 20
        self.bgcolor = "rgba(25, 20, 35, 0.7)"
        self.blur = ft.Blur(30, 30) # 高强度毛玻璃
        self.border_radius = ft.border_radius.only(top_left=24, bottom_left=24)
        self.border = ft.border.all(1, "rgba(255, 255, 255, 0.1)")
        self.shadow = ft.BoxShadow(
            spread_radius=1,
            blur_radius=40,
            color=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            offset=ft.Offset(-10, 0)
        )
        self.animate_offset = ft.Animation(400, ft.AnimationCurve.EASE_OUT_BACK)
        self.animate = ft.Animation(400, ft.AnimationCurve.DECELERATE)
        
        self._build_ui()

    def _build_ui(self):
        # 头部：标题、固钉、关闭
        self.pin_btn = ft.IconButton(
            ft.Icons.PUSH_PIN_OUTLINED, 
            icon_size=16, 
            on_click=self._toggle_pin,
            tooltip="固钉模式 (点击外部不自动收起)"
        )

        self.header = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.INFO_OUTLINED, size=18, color=GenshinTheme.PRIMARY),
                    ft.Text("详细审计", size=16, weight=ft.FontWeight.BOLD),
                ], spacing=12),
                
                ft.Row([
                    self.pin_btn,
                    ft.IconButton(
                        ft.Icons.CLOSE_ROUNDED, 
                        icon_size=20, 
                        on_click=lambda _: self.hide()
                    ),
                ], spacing=5)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=20, vertical=15),
            border=ft.border.only(bottom=ft.border.BorderSide(1, "rgba(255, 255, 255, 0.05)"))
        )

        # 内容滚动容器
        self.detail_area = ft.Column(
            expand=True,
            scroll=ft.ScrollMode.ADAPTIVE,
            spacing=20
        )

        self.content = ft.Column([
            self.header,
            ft.Container(content=self.detail_area, padding=20, expand=True)
        ], spacing=0, expand=True)

    def show(self, content: Optional[ft.Control] = None, title: str = "详细审计"):
        """从右侧滑出抽屉"""
        if content:
            self.detail_area.controls = [content]
        self.header.content.controls[0].controls[1].value = title
        
        self.right = 0
        self.update()

    def hide(self):
        """滑回右侧边缘外"""
        if self.is_pinned: return # 固钉态下禁止点击外部或关闭按钮触发自动隐藏（可选）
        self.right = -self.drawer_width
        self.update()

    def _toggle_pin(self, e):
        self.is_pinned = not self.is_pinned
        self.pin_btn.icon = ft.Icons.PUSH_PIN if self.is_pinned else ft.Icons.PUSH_PIN_OUTLINED
        self.pin_btn.icon_color = GenshinTheme.PRIMARY if self.is_pinned else None
        
        # 固钉态视觉反馈：加深边框
        self.border = ft.border.all(
            2 if self.is_pinned else 1, 
            GenshinTheme.PRIMARY if self.is_pinned else "rgba(255, 255, 255, 0.1)"
        )
        self.update()
