import flet as ft
from ui.states.app_state import AppState
from ui.theme import GenshinTheme
from core.logger import get_ui_logger
from ui.views.analysis_view import AnalysisView
from ui.views.strategic_view import StrategicView
from ui.views.tactical_view import TacticalView
from ui.views.scene_view import SceneView


class AppLayout:
    """
    高度响应式布局：支持战略/战术全屏功能切换
    """

    def __init__(self, page: ft.Page, state: AppState):
        self.page = page
        self.state = state
        self.current_phase = None

        GenshinTheme.apply_page_settings(self.page)

        # 1.5 实例化重构版组件 (类名已去Reboot化)
        self.strategic_reboot = StrategicView(self.state)
        self.scene_reboot = SceneView(self.state)
        self.tactical_reboot = TacticalView(self.state)
        self.analysis_reboot = AnalysisView()

        # 旧版切换器已弃用，重构版通过全屏 Middle Pane 切换
        self.left_switcher = ft.Container()
        self.middle_switcher = ft.AnimatedSwitcher(
            content=self.strategic_reboot, expand=True
        )
        self.right_switcher = ft.Container()

        # 2.5 阶段专用工具容器 (用于注入复盘页的布局切换等按钮)
        self.phase_tools = ft.Container(animate=ft.Animation(300, ft.AnimationCurve.DECELERATE))

        self.header = self._build_header()
        self.footer = self._build_footer()

        # 3. 三栏容器
        self.left_pane_container = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=self.left_switcher, padding=ft.padding.all(24), expand=True
                ),
                variant=ft.CardVariant.ELEVATED,
                bgcolor=GenshinTheme.SURFACE,
            ),
            width=300,
            animate=ft.Animation(400, ft.AnimationCurve.DECELERATE),
        )
        self.middle_pane = ft.Card(
            content=ft.Container(content=self.middle_switcher, padding=24, expand=True),
            variant=ft.CardVariant.ELEVATED,
            bgcolor=GenshinTheme.SURFACE,
            expand=True,
        )
        self.right_pane_container = ft.Container(
            content=ft.Card(
                content=ft.Container(
                    content=self.right_switcher, padding=ft.padding.all(24), expand=True
                ),
                variant=ft.CardVariant.ELEVATED,
                bgcolor=GenshinTheme.SURFACE,
            ),
            width=380,
            animate=ft.Animation(400, ft.AnimationCurve.DECELERATE),
        )

        self._setup_state_bridge()
        self.page.on_resize = self._handle_resize
        
        # 4. 启动即进入重构版战略视图 (同步调用)
        self.handle_nav_click("strategic")

    def _handle_resize(self, e):
        width = float(e.width)
        new_l = width < 1400
        new_r = width < 1000
        if (
            self.state.sidebar_collapsed != new_l
            or self.state.visual_collapsed != new_r
        ):
            self.state.sidebar_collapsed = new_l
            self.state.visual_collapsed = new_r
            self.state.refresh()

    def _setup_state_bridge(self):
        # 1. 订阅物理布局变更 (如侧边栏折叠)
        def update_layout():
            is_l = self.state.sidebar_collapsed
            is_r = self.state.visual_collapsed
            self.left_pane_container.width = 80 if is_l else 300
            self.right_pane_container.width = 60 if is_r else 380
            
            try:
                self.left_pane_container.content.content.padding = (
                    ft.padding.all(12) if is_l else ft.padding.all(24)
                )
                self.right_pane_container.content.content.padding = (
                    ft.padding.all(8) if is_r else ft.padding.all(24)
                )
            except: pass
            self.page.update()

        # 2. 订阅仿真进度变更
        def update_simulation():
            try:
                self.status_text.value = self.state.sim_status
                self.progress_bar.value = self.state.sim_progress
                self.progress_bar.visible = self.state.is_simulating
                self.page.update()
            except: pass

        # 3. 订阅各业务模块变更
        def on_strategic_change():
            if self.current_phase == "strategic":
                self.strategic_reboot._refresh_all()

        def on_scene_change():
            if self.current_phase == "scene":
                self.scene_reboot._refresh_all()

        def on_tactical_change():
            if self.current_phase == "tactical":
                self.tactical_reboot._refresh_all()

        def on_simulation_finished():
            # 当仿真状态变为 IDLE 且有 session_id 时，触发分析页加载
            if self.state.sim_status.startswith("FINISHED"):
                self.analysis_reboot.refresh_data()

        # 执行订阅
        self.state.events.subscribe("global", update_layout)
        self.state.events.subscribe("simulation", update_simulation)
        self.state.events.subscribe("simulation", on_simulation_finished)
        self.state.events.subscribe("strategic", on_strategic_change)
        self.state.events.subscribe("scene", on_scene_change)
        self.state.events.subscribe("tactical", on_tactical_change)

    def handle_nav_click(self, phase_id):
        if self.current_phase == phase_id:
            return
        self.current_phase = phase_id
        
        # 1. 基础布局复位
        self.left_pane_container.visible = True
        self.right_pane_container.visible = True
        self.middle_pane.variant = ft.CardVariant.ELEVATED
        self.middle_pane.content.padding = 24
        self.phase_tools.content = None

        if phase_id == "strategic":
            # 重构版：隐藏左右栏，全屏展示
            self.left_pane_container.visible = False
            self.right_pane_container.visible = False
            self.middle_pane.variant = ft.CardVariant.FILLED
            self.middle_pane.bgcolor = ft.Colors.TRANSPARENT
            self.middle_pane.content.padding = 0
            self.middle_switcher.content = self.strategic_reboot
        elif phase_id == "scene":
            # 场景视图：全屏展示
            self.left_pane_container.visible = False
            self.right_pane_container.visible = False
            self.middle_pane.variant = ft.CardVariant.FILLED
            self.middle_pane.bgcolor = ft.Colors.TRANSPARENT
            self.middle_pane.content.padding = 0
            self.middle_switcher.content = self.scene_reboot
        elif phase_id == "tactical":
            # 重构版战术：全屏展示
            self.left_pane_container.visible = False
            self.right_pane_container.visible = False
            self.middle_pane.variant = ft.CardVariant.FILLED
            self.middle_pane.bgcolor = ft.Colors.TRANSPARENT
            self.middle_pane.content.padding = 0
            self.middle_switcher.content = self.tactical_reboot
        elif phase_id == "review":
            # 重构版分析：全屏展示
            self.left_pane_container.visible = False
            self.right_pane_container.visible = False
            self.middle_pane.variant = ft.CardVariant.FILLED
            self.middle_pane.bgcolor = ft.Colors.TRANSPARENT
            self.middle_pane.content.padding = 0
            
            self.middle_switcher.content = self.analysis_reboot
            # 这里的工具按钮后续可以适配新的 AnalysisViewReboot
            self.phase_tools.content = None

        self.header.content.controls[1].content.controls = [
            self._build_nav_item(text, pid, icon) for text, pid, icon in self.nav_items
        ]
        self.state.refresh()

    def _build_header(self):
        self.nav_items = [
            ("战略", "strategic", ft.Icons.SETTINGS_INPUT_COMPONENT),
            ("场景", "scene", ft.Icons.PUBLIC),
            ("战术", "tactical", ft.Icons.TIMELINE),
            ("复盘", "review", ft.Icons.ANALYTICS),
        ]
        self.nav_row = ft.Row(
            [
                self._build_nav_item(text, pid, icon)
                for text, pid, icon in self.nav_items
            ],
            spacing=4,
            tight=True,
        )
        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=4,
                                height=20,
                                bgcolor=ft.Colors.PRIMARY,
                                border_radius=2,
                            ),
                            ft.Text(
                                "GENSHIN WORKBENCH",
                                size=13,
                                weight=ft.FontWeight.W_900,
                                color=GenshinTheme.ON_SURFACE,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Container(
                        content=self.nav_row,
                        bgcolor="rgba(0, 0, 0, 0.2)",
                        border_radius=30,
                        padding=4,
                        border=ft.border.all(1, "rgba(255, 255, 255, 0.05)"),
                    ),
                    ft.Row(
                        [
                            self.phase_tools,
                            ft.VerticalDivider(width=1, color="rgba(255,255,255,0.1)"),
                            ft.IconButton(
                                ft.Icons.SAVE_OUTLINED,
                                on_click=lambda _: self.page.run_task(self.page.persistence.save_config),
                            ),
                            ft.IconButton(
                                ft.Icons.FOLDER_OPEN_OUTLINED,
                                on_click=lambda _: self.page.run_task(self.page.persistence.load_config),
                            ),
                        ],
                        spacing=5,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=12),
            bgcolor=GenshinTheme.HEADER_BG,
            blur=ft.Blur(20, 20),
            border=ft.border.only(bottom=ft.BorderSide(1, GenshinTheme.GLASS_BORDER)),
        )

    def _build_nav_item(self, text, phase_id, icon):
        is_active = self.current_phase == phase_id
        active_color = ft.Colors.PRIMARY
        idle_color = "rgba(255,255,255,0.55)"

        # 底部指示线：激活时高度 3px，非激活时 0px，带动画
        indicator = ft.Container(
            width=36,
            height=3 if is_active else 0,
            bgcolor=active_color,
            border_radius=2,
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        )

        label_row = ft.Row(
            [
                ft.Icon(
                    icon,
                    size=18 if is_active else 15,
                    color=active_color if is_active else idle_color,
                ),
                ft.Text(
                    text,
                    size=13 if is_active else 12,
                    weight=ft.FontWeight.W_900 if is_active else ft.FontWeight.W_400,
                    color=active_color if is_active else idle_color,
                ),
            ],
            spacing=7,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        return ft.Container(
            content=ft.Column(
                [label_row, indicator],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            width=100,
            height=42,
            bgcolor="rgba(209, 162, 255, 0.12)" if is_active else "transparent",
            border_radius=20,
            padding=ft.padding.only(top=4, bottom=4),
            on_click=lambda _: self.handle_nav_click(phase_id),
            animate=ft.Animation(300, ft.AnimationCurve.DECELERATE),
        )

    def _build_footer(self):
        # 初始化状态反馈组件
        self.status_text = ft.Text(
            self.state.sim_status,
            size=11,
            weight=ft.FontWeight.BOLD,
            opacity=0.8,
            color=GenshinTheme.ON_SURFACE,
        )
        self.progress_bar = ft.ProgressBar(
            width=120,
            value=0,
            bgcolor="rgba(255,255,255,0.1)",
            color=GenshinTheme.PRIMARY,
            visible=False,
        )

        return ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                width=12,
                                height=12,
                                bgcolor=GenshinTheme.ELEMENT_COLORS["Dendro"],
                                border_radius=6,
                            ),
                            ft.Column(
                                [self.status_text, self.progress_bar],
                                spacing=2,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "批处理",
                                icon=ft.Icons.ACCOUNT_TREE,
                                on_click=self._launch_universe,
                            ),
                            ft.ElevatedButton(
                                "开始仿真",
                                bgcolor=ft.Colors.PRIMARY,
                                color=GenshinTheme.ON_PRIMARY,
                                height=40,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12)
                                ),
                                on_click=lambda _: self.page.run_task(
                                    self.state.run_simulation
                                ),
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding(40, 4, 40, 4),
            bgcolor=GenshinTheme.FOOTER_BG,
            blur=ft.Blur(20, 20),
            border=ft.border.only(top=ft.BorderSide(1, GenshinTheme.GLASS_BORDER)),
            height=50,
        )

    def _launch_universe(self, e):
        """核心：启动指挥部并同步当前基准配置"""
        try:
            from ui.universe_launcher import start_universe_process
            import multiprocessing
            import asyncio

            # 1. 启动子进程 (传入双向队列)
            p = multiprocessing.Process(
                target=start_universe_process,
                args=(self.state.main_to_branch, self.state.branch_to_main),
                daemon=True,
            )
            p.start()

            # 2. 延迟一下确保子进程已启动监听，然后发送当前配置
            async def sync_task():
                await asyncio.sleep(1.0)
                self.state.launch_commander()

            self.page.run_task(sync_task)
            get_ui_logger().log_info(f"Commander launched. PID: {p.pid}")
        except Exception as ex:
            get_ui_logger().log_error(f"Failed to launch native window: {ex}")

    def build(self):
        content_row = ft.Row(
            [self.left_pane_container, self.middle_pane, self.right_pane_container],
            spacing=10,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )
        content_area = ft.Container(content=content_row, padding=ft.Padding(6, 6, 6, 6), expand=True)

        def on_connect(e):
            self._handle_resize(
                ft.ControlEvent(
                    target="page",
                    name="resize",
                    data="",
                    control=self.page,
                    page=self.page,
                )
            )
            self.state.refresh()

        self.page.on_connect = on_connect
        return ft.Column(
            [self.header, content_area, self.footer], spacing=0, expand=True
        )


async def main(page: ft.Page):
    state = AppState()
    state.register_page(page)
    layout = AppLayout(page, state)
    page.add(layout.build())


if __name__ == "__main__":
    ft.app(target=main)
