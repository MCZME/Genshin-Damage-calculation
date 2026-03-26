from __future__ import annotations
import flet as ft
from typing import TYPE_CHECKING
from ui.states.analysis_state import AnalysisState
from ui.states.settings_state import SettingsState
from ui.theme import GenshinTheme
from core.logger import get_ui_logger
from ui.views.analysis_view import AnalysisView
from ui.views.strategic_view import StrategicView
from ui.views.tactical_view import TacticalView
from ui.views.scene_view import SceneView
from ui.components.settings.settings_dialog import SettingsDialog
from ui.view_models.settings_vm import SettingsViewModel

if TYPE_CHECKING:
    from ui.states.app_state import AppState
    from ui.view_models.layout_vm import LayoutViewModel
    from ui.services.persistence_manager import PersistenceManager


class AppLayout:
    """
    高度响应式布局 (MVVM 重构版 V5.0)
    已修复：采用多视图 Stack + Visibility 模式，根治切换后的 RuntimeError。
    """
    def __init__(self, page: ft.Page, state: AppState, persistence: PersistenceManager):
        self.page = page
        self.state = state
        self.persistence = persistence
        GenshinTheme.apply_page_settings(self.page)

    @ft.component
    def build(self, vm: LayoutViewModel):
        active_phase = vm.current_phase
        get_ui_logger().log_debug(f"AppLayout build triggered. Active Phase: {active_phase}")

        # 1. 视图实例持久化
        strat_view = ft.use_memo(lambda: StrategicView(self.state), [])
        scene_view = ft.use_memo(lambda: SceneView(self.state), [])
        tact_view = ft.use_memo(lambda: TacticalView(self.state), [])

        # AnalysisState 专用 (保持动态 build 因为其数据量大且生命周期独立)
        analysis_state = ft.use_memo(lambda: AnalysisState(self.state), [])
        analysis_view = ft.use_memo(lambda: AnalysisView(self.state), [])

        # 设置状态
        settings_state = ft.use_memo(lambda: SettingsState(), [])
        settings_vm = ft.use_memo(lambda: SettingsViewModel(), [])

        # 2. 导航处理逻辑
        def handle_nav(pid):
            get_ui_logger().log_info(f"Navigating to: {pid}")
            vm.switch_tab(pid)
            if pid == "review":
                analysis_state.refresh_data()

        # 3. 构建导航项
        nav_items_data = [
            ("战略", "strategic", ft.Icons.SETTINGS_INPUT_COMPONENT),
            ("场景", "scene", ft.Icons.PUBLIC),
            ("战术", "tactical", ft.Icons.TIMELINE),
            ("复盘", "review", ft.Icons.ANALYTICS),
        ]
        
        def create_nav_btn(label: str, pid: str, icon: ft.IconData, is_active: bool) -> ft.Control:
            return self._build_nav_item_declarative(label, pid, icon, is_active, handle_nav)

        nav_controls: list[ft.Control] = [
            create_nav_btn(label, phase_id, icon, active_phase == phase_id) 
            for label, phase_id, icon in nav_items_data
        ]

        # 4. 核心渲染策略重构：
        # 使用 Stack + Visibility 模式，确保所有 View 的控件始终在 Page 中注册。
        # 这样能彻底防止 "Control must be added to the page first" 报错。
        
        main_content_stack = ft.Stack([
            # 战略视图
            ft.Container(
                content=strat_view.build(self.state.strategic_state),
                visible=(active_phase == "strategic"),
                expand=True
            ),
            # 场景视图
            ft.Container(
                content=scene_view.build(self.state.strategic_state),
                visible=(active_phase == "scene"),
                expand=True
            ),
            # 战术视图
            ft.Container(
                content=tact_view.build(self.state.tactical_state),
                visible=(active_phase == "tactical"),
                expand=True
            ),
            # 复盘视图 (动态渲染)
            ft.Container(
                content=analysis_view.build(analysis_state) if active_phase == "review" else ft.Container(),
                visible=(active_phase == "review"),
                expand=True
            )
        ], expand=True)

        header = self._build_header_declarative(nav_controls, vm)
        footer = self._build_footer_declarative()

        # 同步设置对话框状态
        def sync_settings_open():
            if settings_vm.is_open != vm.settings_open:
                settings_vm.is_open = vm.settings_open
                settings_vm.notify_update()
        ft.use_effect(sync_settings_open, [vm.settings_open])

        return ft.Stack([
            ft.Column([
                header,
                ft.Container(content=main_content_stack, padding=6, expand=True),
                footer
            ], spacing=0, expand=True),
            SettingsDialog(vm=settings_vm, state=settings_state, page=self.page),
        ], expand=True)

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

    def _build_header_declarative(self, nav_controls: list[ft.Control], vm: "LayoutViewModel") -> ft.Control:
        header_left_controls: list[ft.Control] = [
            ft.Container(width=4, height=20, bgcolor=ft.Colors.PRIMARY, border_radius=2),
            ft.Text("GENSHIN WORKBENCH", size=13, weight=ft.FontWeight.W_900, color=GenshinTheme.ON_SURFACE),
        ]
        
        header_right_controls: list[ft.Control] = [
            ft.IconButton(
                ft.Icons.ACCOUNT_TREE_OUTLINED,
                tooltip="打开批处理编辑器",
                on_click=lambda _: self.page.run_task(getattr(self.page, "open_batch_editor")),
            ),
            ft.IconButton(
                ft.Icons.SETTINGS_OUTLINED,
                tooltip="系统设置",
                on_click=lambda _: vm.toggle_settings(),
            ),
            ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=lambda _: self.page.run_task(self.persistence.save_config)),
            ft.IconButton(ft.Icons.FOLDER_OPEN_OUTLINED, on_click=lambda _: self.page.run_task(self.persistence.load_config)),
        ]

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(controls=header_left_controls, spacing=12),
                    ft.Container(
                        content=ft.Row(controls=nav_controls, spacing=4, tight=True), 
                        bgcolor="rgba(0, 0, 0, 0.2)", 
                        border_radius=30, 
                        padding=4, 
                        border=ft.border.all(1, "rgba(255, 255, 255, 0.05)")
                    ),
                    ft.Row(controls=header_right_controls, spacing=5)
                ], 
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding.symmetric(horizontal=32, vertical=12), 
            bgcolor=GenshinTheme.HEADER_BG, 
            blur=20, 
            border=ft.border.only(bottom=ft.BorderSide(1, GenshinTheme.GLASS_BORDER))
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
