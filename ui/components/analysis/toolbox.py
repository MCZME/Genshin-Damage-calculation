import flet as ft
from ui.theme import GenshinTheme

class AnalysisToolbox(ft.Container):
    """
    分析工具箱。
    提供磁贴资源库的开关入口及预设方案。
    """
    def __init__(self, on_tile_toggle=None):
        super().__init__()
        self.on_tile_toggle = on_tile_toggle
        self.is_expanded = False # 默认收起
        self.tool_items: dict[str, ft.Container] = {} 
        
        # 基础样式
        self.width = 72
        self.bgcolor = "#1A1625"
        self.border = ft.border.only(right=ft.border.BorderSide(1, "rgba(255, 255, 255, 0.05)"))
        self.animate = ft.Animation(400, ft.AnimationCurve.EASE_OUT_QUINT)
        
        self._build_ui()

    def _build_ui(self):
        # 1. 顶部菜单按钮与标题
        self.toggle_btn = ft.IconButton(
            ft.Icons.MENU_ROUNDED,
            icon_size=20,
            on_click=self._handle_collapse,
            style=ft.ButtonStyle(shape=ft.CircleBorder())
        )
        self.toggle_label = ft.Container(
            content=ft.Text("MENU", size=14, weight=ft.FontWeight.W_900, color=ft.Colors.WHITE, style=ft.TextStyle(letter_spacing=2)),
            opacity=0,
            animate_opacity=300,
            margin=ft.margin.only(left=15)
        )
        
        self.header_row = ft.Container(
            content=ft.Row([
                ft.Container(self.toggle_btn, width=48, alignment=ft.Alignment.CENTER),
                self.toggle_label
            ], spacing=0, tight=True),
            height=60,
            padding=ft.padding.only(left=12)
        )

        # 2. 磁贴项配置 (扁平化列表)
        self.items_config = [
            ("DPS 曲线", ft.Icons.AUTO_GRAPH_ROUNDED, "dps"),
            ("全局战报", ft.Icons.DASHBOARD_ROUNDED, "summary"),
            ("多轨时间轴", ft.Icons.VIEW_TIMELINE_ROUNDED, "timeline"),
            ("物理重演", ft.Icons.VIDEOGAME_ASSET_ROUNDED, "replay"),
            ("能量水位", ft.Icons.BOLT_ROUNDED, "energy"),
        ]

        # 构建中间列表
        self.menu_list = ft.Column(spacing=8, scroll=ft.ScrollMode.HIDDEN)
        for label, icon, tid in self.items_config:
            item = self._build_menu_item(label, icon, tid)
            self.tool_items[tid] = item
            self.menu_list.controls.append(item)

        # 3. 底部固定项
        self.preset_section = ft.Column([
            ft.Divider(height=1, color="rgba(255,255,255,0.05)"),
            self._build_menu_item("排轴预设", ft.Icons.AUTO_AWESOME_MOTION_ROUNDED, "preset_rotation"),
            self._build_menu_item("设置", ft.Icons.SETTINGS_ROUNDED, "settings"),
        ], spacing=5)

        self.content = ft.Column([
            self.header_row,
            ft.Container(self.menu_list, expand=True, padding=ft.padding.symmetric(horizontal=12)),
            ft.Container(self.preset_section, padding=ft.padding.all(12))
        ], spacing=0)

    def _build_menu_item(self, label: str, icon: str, tid: str):
        # 使用 Container 包装 Row 以实现复杂的 Hover 和状态效果
        icon_ctrl = ft.Icon(icon, size=20, color=ft.Colors.WHITE70)
        label_ctrl = ft.Container(
            content=ft.Text(label, size=13, weight=ft.FontWeight.W_500, no_wrap=True, color=ft.Colors.WHITE70),
            opacity=0,
            animate_opacity=300,
            margin=ft.margin.only(left=15)
        )

        item = ft.Container(
            content=ft.Row([
                ft.Container(icon_ctrl, width=48, alignment=ft.Alignment.CENTER),
                label_ctrl
            ], spacing=0, tight=True),
            height=48,
            border_radius=12,
            on_click=lambda _: self.on_tile_toggle(tid) if self.on_tile_toggle else None,
            on_hover=self._handle_item_hover,
            animate=ft.Animation(200, ft.AnimationCurve.DECELERATE),
        )
        return item

    def _handle_item_hover(self, e):
        # 悬停时背景微亮
        e.control.bgcolor = "rgba(255, 255, 255, 0.05)" if e.data == "true" else "transparent"
        try:
            e.control.update()
        except:
            pass

    def _handle_collapse(self, e):
        self.is_expanded = not self.is_expanded
        self.width = 220 if self.is_expanded else 72
        self.toggle_btn.icon = ft.Icons.MENU_OPEN_ROUNDED if self.is_expanded else ft.Icons.MENU_ROUNDED
        
        # 顶部标签可见度
        self.toggle_label.opacity = 1 if self.is_expanded else 0
        
        # 切换所有文字的可见度 (不再包含组标题逻辑)
        for ctrl in self.menu_list.controls:
            if isinstance(ctrl, ft.Container) and isinstance(ctrl.content, ft.Row):
                ctrl.content.controls[1].opacity = 1 if self.is_expanded else 0
        
        # 底部项处理
        for item in self.preset_section.controls:
            if isinstance(item, ft.Container) and isinstance(item.content, ft.Row):
                item.content.controls[1].opacity = 1 if self.is_expanded else 0

        try:
            self.update()
        except:
            pass

    def update_active_states(self, active_ids: list[str]):
        """更新磁贴激活状态的视觉反馈"""
        for tid, item in self.tool_items.items():
            is_active = tid in active_ids
            # 激活时：背景变淡紫色，图标变主色
            item.bgcolor = "rgba(209, 162, 255, 0.15)" if is_active else "transparent"
            item.content.controls[0].content.color = GenshinTheme.PRIMARY if is_active else ft.Colors.WHITE70
            item.content.controls[1].content.color = ft.Colors.WHITE if is_active else ft.Colors.WHITE70
        self.update()
