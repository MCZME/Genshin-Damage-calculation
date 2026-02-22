import flet as ft

class TargetSidebarSlot(ft.Container):
    """
    敌方目标侧边栏槽位组件 (原子化重构版)。
    支持显示目标索引、名称、等级及删除按钮。
    """
    def __init__(
        self, 
        index: int, 
        target: dict, 
        is_selected: bool = False,
        on_click = None,
        on_remove = None
    ):
        super().__init__()
        self.index = index
        self.target = target
        self.is_selected = is_selected
        self.on_click_callback = on_click
        self.on_remove_callback = on_remove
        
        self._build_ui()

    def _build_ui(self):
        theme_color = ft.Colors.RED_400 if self.is_selected else ft.Colors.RED_900
        
        bg_opacity = 0.28 if self.is_selected else 0.10
        bg_gradient = ft.LinearGradient(
            begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
            colors=[
                ft.Colors.with_opacity(bg_opacity, theme_color), 
                ft.Colors.with_opacity(bg_opacity * 0.3, theme_color)
            ]
        )

        # 索引图标 (代替头像)
        avatar = ft.Container(
            content=ft.Text(str(self.index + 1), size=15, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE),
            width=36, height=36, bgcolor=ft.Colors.with_opacity(0.3, theme_color),
            border_radius=18, alignment=ft.Alignment.CENTER,
            border=ft.Border.all(1.5, ft.Colors.with_opacity(0.6 if self.is_selected else 0.25, theme_color))
        )

        name_col = ft.Column([
            ft.Text(self.target['name'], size=13, weight=ft.FontWeight.W_900 if self.is_selected else ft.FontWeight.BOLD),
            ft.Text(f"Lv.{self.target['level']}", size=10, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE)),
        ], spacing=1, expand=True)

        remove_btn = ft.Container(
            content=ft.Icon(ft.Icons.CLOSE, size=11, color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE)),
            width=22, height=22, border_radius=11, alignment=ft.Alignment.CENTER,
            on_click=self._on_remove_click,
        )
        remove_btn.mouse_cursor = ft.MouseCursor.CLICK

        self.content = ft.Stack([
            ft.Container(expand=True, gradient=bg_gradient, border_radius=12),
            ft.Container(
                content=ft.Row([avatar, name_col, remove_btn], spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding(11, 11, 11, 11)
            )
        ])
        
        self.height = 60
        self.border_radius = 12
        self.border = ft.Border.all(2 if self.is_selected else 1, ft.Colors.with_opacity(0.65 if self.is_selected else 0.12, theme_color))
        self.shadow = ft.BoxShadow(spread_radius=1, blur_radius=15, color=ft.Colors.with_opacity(0.5, theme_color)) if self.is_selected else None
        self.on_click = lambda _: self.on_click_callback(self.index) if self.on_click_callback else None
        self.offset = ft.Offset(0.04, 0) if self.is_selected else ft.Offset(0, 0)
        self.animate = ft.Animation(300, ft.AnimationCurve.DECELERATE)
        self.animate_offset = ft.Animation(300, ft.AnimationCurve.EASE_OUT_BACK)
        self.mouse_cursor = ft.MouseCursor.CLICK

    def _on_remove_click(self, e):
        e.control.page = self.page
        if self.on_remove_callback:
            self.on_remove_callback(self.index)

    def update_state(self, target: dict, is_selected: bool):
        """精准同步状态"""
        self.target = target
        self.is_selected = is_selected
        self._build_ui()
        try: self.update()
        except: pass
