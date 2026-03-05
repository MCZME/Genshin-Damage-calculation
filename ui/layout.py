import flet as ft
from ui.states.analysis_state import AnalysisState
from ui.states.app_state import AppState
from ui.theme import GenshinTheme
from core.logger import get_ui_logger
from ui.views.analysis_view import AnalysisView
from ui.views.strategic_view import StrategicView
from ui.views.tactical_view import TacticalView
from ui.views.scene_view import SceneView


class AppLayout:
    """
    高度响应式布局 (声明式重构版)
    """
    def __init__(self, page: ft.Page, state: AppState):
        self.page = page
        self.state = state
        GenshinTheme.apply_page_settings(self.page)
        
        self._dirty_views = {"strategic": True, "scene": True, "tactical": True}

    @ft.component
    def build(self):
        # 1. 局部状态管理 (过渡阶段默认打开分析界面)
        current_phase, set_current_phase = ft.use_state("review")
        self.current_phase = current_phase 

        # 2. 持久化 State 实例 (提取出来，防止被 Component 包装隐藏)
        analysis_state = ft.use_memo(lambda: AnalysisState(app_state=self.state), [])

        # 3. 持久化 View 实例
        views = ft.use_memo(lambda: {
            "strategic": StrategicView(self.state),
            "scene": SceneView(self.state),
            "tactical": TacticalView(self.state),
            "review": AnalysisView(self.state, state=analysis_state) # 注入状态
        }, [])
        
        self.strategic_reboot = views["strategic"]
        self.scene_reboot = views["scene"]
        self.tactical_reboot = views["tactical"]
        self.analysis_reboot = views["review"]

        # 4. 导航逻辑 (直接操作 analysis_state)
        def handle_nav(pid):
            set_current_phase(pid)
            if pid == "strategic" and self._dirty_views.get("strategic"):
                self.strategic_reboot._refresh_all(); self._dirty_views["strategic"] = False
            elif pid == "scene" and self._dirty_views.get("scene"):
                self.scene_reboot._refresh_all(); self._dirty_views["scene"] = False
            elif pid == "tactical" and self._dirty_views.get("tactical"):
                self.tactical_reboot._refresh_all(); self._dirty_views["tactical"] = False
            elif pid == "review":
                analysis_state.refresh_data() # 直接调用，修复报错

        # 4. 构建声明式组件
        nav_items_data = [
            ("战略", "strategic", ft.Icons.SETTINGS_INPUT_COMPONENT),
            ("场景", "scene", ft.Icons.PUBLIC),
            ("战术", "tactical", ft.Icons.TIMELINE),
            ("复盘", "review", ft.Icons.ANALYTICS),
        ]
        
        nav_controls = [
            self._build_nav_item_declarative(text, pid, icon, current_phase == pid, handle_nav)
            for text, pid, icon in nav_items_data
        ]

        header = self._build_header_declarative(nav_controls)
        footer = self._build_footer_declarative()
        
        # 确定当前活动内容
        active_view = views.get(current_phase, views["strategic"])
        # 如果是新版声明式类（非 ft.Control），必须显式调用 .build() 获取组件
        renderable_view = active_view.build() if not isinstance(active_view, ft.Control) else active_view

        return ft.Column([
            header,
            ft.Container(content=renderable_view, padding=6, expand=True),
            footer
        ], spacing=0, expand=True)

    def _build_nav_item_declarative(self, text, pid, icon, is_active, on_click):
        active_color = ft.Colors.PRIMARY
        idle_color = "rgba(255,255,255,0.55)"
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(icon, size=18 if is_active else 15, color=active_color if is_active else idle_color),
                    ft.Text(text, size=13 if is_active else 12, weight=ft.FontWeight.W_900 if is_active else ft.FontWeight.W_400, color=active_color if is_active else idle_color),
                ], spacing=7, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(width=36, height=3 if is_active else 0, bgcolor=active_color, border_radius=2, animate=300)
            ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER),
            width=100, height=42, bgcolor="rgba(209, 162, 255, 0.12)" if is_active else "transparent",
            border_radius=20, on_click=lambda _: on_click(pid), animate=300
        )

    def _build_header_declarative(self, nav_controls):
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(width=4, height=20, bgcolor=ft.Colors.PRIMARY, border_radius=2),
                    ft.Text("GENSHIN WORKBENCH", size=13, weight=ft.FontWeight.W_900, color=GenshinTheme.ON_SURFACE),
                ], spacing=12),
                ft.Container(content=ft.Row(nav_controls, spacing=4, tight=True), bgcolor="rgba(0, 0, 0, 0.2)", border_radius=30, padding=4, border=ft.border.all(1, "rgba(255, 255, 255, 0.05)")),
                ft.Row([
                    ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=lambda _: self.page.run_task(self.page.persistence.save_config)),
                    ft.IconButton(ft.Icons.FOLDER_OPEN_OUTLINED, on_click=lambda _: self.page.run_task(self.page.persistence.load_config)),
                ], spacing=5)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding.symmetric(horizontal=32, vertical=12), bgcolor=GenshinTheme.HEADER_BG, blur=20, border=ft.border.only(bottom=ft.BorderSide(1, GenshinTheme.GLASS_BORDER))
        )

    def _build_footer_declarative(self):
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(width=12, height=12, bgcolor=GenshinTheme.ELEMENT_COLORS["Dendro"], border_radius=6),
                    ft.Text(self.state.sim_status, size=11, weight=ft.FontWeight.BOLD, color=GenshinTheme.ON_SURFACE),
                ], spacing=10),
                ft.Row([
                    ft.ElevatedButton("开始仿真", bgcolor=ft.Colors.PRIMARY, color=GenshinTheme.ON_PRIMARY, height=40, on_click=lambda _: self.page.run_task(self.state.run_simulation)),
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(40, 4, 40, 4), bgcolor=GenshinTheme.FOOTER_BG, height=50, border=ft.border.only(top=ft.BorderSide(1, GenshinTheme.GLASS_BORDER))
        )
