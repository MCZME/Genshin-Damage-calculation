import flet as ft
from typing import Optional
from ui.state import AppState
from ui.theme import GenshinTheme
from ui.components.entity_pool import EntityPool
from ui.components.property_editor import PropertyEditor
from ui.components.visual_pane import VisualPane
from ui.components.action_library import ActionLibrary
from ui.components.timeline_sequence import TimelineSequence
from ui.components.action_inspector import ActionInspector

class AppLayout:
    """
    高度响应式布局：支持战略/战术全屏功能切换
    """
    def __init__(self, page: ft.Page, state: AppState):
        self.page = page
        self.state = state
        self.current_phase = "strategic"
        
        GenshinTheme.apply_page_settings(self.page)
        
        # 1. 实例化业务组件
        self.entity_pool = EntityPool(state)
        self.property_editor = PropertyEditor(state)
        self.visual_pane = VisualPane(state)
        self.action_library = ActionLibrary(state)
        self.timeline_sequence = TimelineSequence(state)
        self.action_inspector = ActionInspector(state)
        
        # 2. 动画切换器
        self.left_switcher = ft.AnimatedSwitcher(content=self.entity_pool, expand=True)
        self.middle_switcher = ft.AnimatedSwitcher(content=self.property_editor, expand=True)
        self.right_switcher = ft.AnimatedSwitcher(content=self.visual_pane, expand=True)
        
        self.header = self._build_header()
        self.footer = self._build_footer()
        
        # 3. 三栏容器
        self.left_pane_container = ft.Container(
            content=ft.Card(content=ft.Container(content=self.left_switcher, padding=ft.padding.all(24), expand=True), variant=ft.CardVariant.ELEVATED, bgcolor=GenshinTheme.SURFACE),
            width=300, animate=ft.Animation(400, ft.AnimationCurve.DECELERATE)
        )
        self.middle_pane = ft.Card(
            content=ft.Container(content=self.middle_switcher, padding=24, expand=True),
            variant=ft.CardVariant.ELEVATED, bgcolor=GenshinTheme.SURFACE, expand=True 
        )
        self.right_pane_container = ft.Container(
            content=ft.Card(content=ft.Container(content=self.right_switcher, padding=ft.padding.all(24), expand=True), variant=ft.CardVariant.ELEVATED, bgcolor=GenshinTheme.SURFACE),
            width=380, animate=ft.Animation(400, ft.AnimationCurve.DECELERATE)
        )

        self._setup_state_bridge()
        self.page.on_resize = self._handle_resize

    def _handle_resize(self, e):
        width = float(e.width)
        new_l = width < 1400
        new_r = width < 1000
        if self.state.sidebar_collapsed != new_l or self.state.visual_collapsed != new_r:
            self.state.sidebar_collapsed = new_l
            self.state.visual_collapsed = new_r
            self.state.refresh()

    def _setup_state_bridge(self):
        original_refresh = self.state.refresh
        def enhanced_refresh():
            # 1. 物理布局同步
            is_l = self.state.sidebar_collapsed
            is_r = self.state.visual_collapsed
            self.left_pane_container.width = 80 if is_l else 300
            self.right_pane_container.width = 60 if is_r else 380
            self.visual_pane.update_size(self.right_pane_container.width - 48, 400)
            
            try:
                self.left_pane_container.content.content.padding = ft.padding.all(12) if is_l else ft.padding.all(24)
                self.right_pane_container.content.content.padding = ft.padding.all(8) if is_r else ft.padding.all(24)
            except: pass
            
            # 2. 仿真进度同步
            try:
                self.status_text.value = self.state.sim_status
                self.progress_bar.value = self.state.sim_progress
                self.progress_bar.visible = self.state.is_simulating
            except: pass

            # 3. 内部组件刷新
            self.entity_pool.is_compact = is_l
            self.visual_pane.is_compact = is_r
            
            if self.current_phase == "strategic":
                self.entity_pool.refresh()
                self.property_editor.refresh()
                self.visual_pane.refresh()
            else:
                self.action_library.refresh()
                self.timeline_sequence.refresh()
                self.action_inspector.refresh()
                
            original_refresh()
        self.state.refresh = enhanced_refresh

    def handle_nav_click(self, phase_id):
        if self.current_phase == phase_id: return
        self.current_phase = phase_id
        if phase_id == "strategic":
            self.left_switcher.content = self.entity_pool
            self.middle_switcher.content = self.property_editor
            self.right_switcher.content = self.visual_pane
        elif phase_id == "tactical":
            self.left_switcher.content = self.action_library
            self.middle_switcher.content = self.timeline_sequence
            self.right_switcher.content = self.action_inspector
        self.header.content.controls[1].content.controls = [self._build_nav_item(text, pid, icon) for text, pid, icon in self.nav_items]
        self.state.refresh()

    def _build_header(self):
        self.nav_items = [("战略", "strategic", ft.Icons.SETTINGS_INPUT_COMPONENT), ("战术", "tactical", ft.Icons.TIMELINE), ("复盘", "review", ft.Icons.ANALYTICS)]
        self.nav_row = ft.Row([self._build_nav_item(text, pid, icon) for text, pid, icon in self.nav_items], spacing=4, tight=True)
        return ft.Container(content=ft.Row([ft.Row([ft.Container(width=4, height=20, bgcolor=ft.Colors.PRIMARY, border_radius=2), ft.Text("GENSHIN WORKBENCH", size=13, weight=ft.FontWeight.W_900, color=GenshinTheme.ON_SURFACE)], spacing=12), ft.Container(content=self.nav_row, bgcolor="rgba(0, 0, 0, 0.2)", border_radius=30, padding=4, border=ft.border.all(1, "rgba(255, 255, 255, 0.05)")), ft.Row([ft.IconButton(ft.Icons.SAVE_OUTLINED, on_click=self._handle_save_dialog), ft.IconButton(ft.Icons.FOLDER_OPEN_OUTLINED, on_click=self._handle_load_dialog)], spacing=5)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=ft.padding.symmetric(horizontal=32, vertical=12), bgcolor=GenshinTheme.HEADER_BG, blur=ft.Blur(20, 20), border=ft.border.only(bottom=ft.BorderSide(1, GenshinTheme.GLASS_BORDER)))

    def _handle_save_dialog(self, e):
        name_f = ft.TextField(label="配置名称", dense=True)
        def confirm(_):
            if name_f.value: self.state.save_config(name_f.value); self.page.pop_dialog()
        self.page.show_dialog(ft.AlertDialog(title=ft.Text("保存配置"), content=name_f, actions=[ft.ElevatedButton("保存", on_click=confirm)]))

    def _handle_load_dialog(self, e):
        configs = self.state.list_configs(); lv = ft.ListView(expand=True, spacing=5, height=300)
        def confirm(fname): self.state.load_config(fname); self.page.pop_dialog()
        for cfg in configs: lv.controls.append(ft.ListTile(title=ft.Text(cfg), on_click=lambda _, n=cfg: confirm(n)))
        self.page.show_dialog(ft.AlertDialog(title=ft.Text("读取配置"), content=ft.Container(lv, width=300)))

    def _build_nav_item(self, text, phase_id, icon):
        is_active = (self.current_phase == phase_id)
        return ft.Container(content=ft.Row([ft.Icon(icon, size=16, color=ft.Colors.PRIMARY if is_active else ft.Colors.WHITE), ft.Text(text, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY if is_active else ft.Colors.WHITE)], spacing=8, alignment=ft.MainAxisAlignment.CENTER), width=100, height=36, bgcolor="rgba(209, 162, 255, 0.15)" if is_active else "transparent", border_radius=20, on_click=lambda _: self.handle_nav_click(phase_id), animate=ft.Animation(300, ft.AnimationCurve.DECELERATE))

    def _build_footer(self):
        # 初始化状态反馈组件
        self.status_text = ft.Text(self.state.sim_status, size=11, weight=ft.FontWeight.BOLD, opacity=0.8, color=GenshinTheme.ON_SURFACE)
        self.progress_bar = ft.ProgressBar(width=120, value=0, bgcolor="rgba(255,255,255,0.1)", color=GenshinTheme.PRIMARY, visible=False)

        return ft.Container(
            content=ft.Row(
                [
                    ft.Row([
                        ft.Container(width=12, height=12, bgcolor=GenshinTheme.ELEMENT_COLORS["Dendro"], border_radius=6),
                        ft.Column([
                            self.status_text,
                            self.progress_bar
                        ], spacing=2, alignment=ft.MainAxisAlignment.CENTER)
                    ], spacing=10),
                    ft.ElevatedButton(
                        "开始仿真", 
                        bgcolor=ft.Colors.PRIMARY, color=GenshinTheme.ON_PRIMARY,
                        height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=lambda _: self.page.run_task(self.state.run_simulation)
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.padding.symmetric(horizontal=40, vertical=8),
            bgcolor=GenshinTheme.FOOTER_BG, blur=ft.Blur(20, 20), border=ft.border.only(top=ft.BorderSide(1, GenshinTheme.GLASS_BORDER)),
            height=64,
        )

    def build(self):
        content_row = ft.Row([self.left_pane_container, self.middle_pane, self.right_pane_container], spacing=10, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        content_area = ft.Container(content=content_row, padding=12, expand=True)
        def on_connect(e): self._handle_resize(ft.ControlEvent(target="page", name="resize", data="", control=self.page, page=self.page)); self.state.refresh()
        self.page.on_connect = on_connect
        return ft.Column([self.header, content_area, self.footer], spacing=0, expand=True)

async def main(page: ft.Page):
    state = AppState(page)
    layout = AppLayout(page, state)
    page.add(layout.build())

if __name__ == "__main__":
    ft.app(target=main)