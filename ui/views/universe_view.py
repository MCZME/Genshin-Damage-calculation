import flet as ft
from ui.theme import GenshinTheme
from core.logger import get_ui_logger
from ui.components.universe_canvas import UniverseCanvas
from ui.components.mutation_inspector import MutationInspector


class UniverseView(ft.Container):
    """
    分支宇宙编辑器视图
    """

    def __init__(self, state):
        super().__init__(expand=True, bgcolor=GenshinTheme.BACKGROUND)
        self.state = state
        self._build_ui()
        self._setup_state_bridge()

    def _setup_state_bridge(self):
        original_refresh = self.state.refresh

        def enhanced_refresh():
            self.refresh()
            original_refresh()

        self.state.refresh = enhanced_refresh

    def _build_ui(self):
        self.canvas = UniverseCanvas(self.state)

        # 导航条
        self.hud = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.AUTO_AWESOME_MOTION,
                                    color=GenshinTheme.PRIMARY,
                                    size=20,
                                ),
                                bgcolor="rgba(209, 162, 255, 0.1)",
                                padding=10,
                                border_radius=12,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "指挥部", size=16, weight=ft.FontWeight.W_900
                                    ),
                                    ft.Text(
                                        "COMMANDER - 变异树编辑器",
                                        size=10,
                                        color=GenshinTheme.TEXT_SECONDARY,
                                    ),
                                ],
                                spacing=-3,
                            ),
                        ],
                        spacing=12,
                    ),
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(
                                    "模拟样本: --",
                                    size=11,
                                    color=GenshinTheme.PRIMARY,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                                bgcolor="rgba(209, 162, 255, 0.05)",
                                border=ft.border.all(1, GenshinTheme.GLASS_BORDER),
                                border_radius=20,
                            ),
                            ft.ElevatedButton(
                                content=ft.Text(
                                    "执行批量仿真", weight=ft.FontWeight.BOLD
                                ),
                                icon=ft.Icons.PLAY_CIRCLE_FILL_ROUNDED,
                                bgcolor=GenshinTheme.PRIMARY,
                                color=GenshinTheme.ON_PRIMARY,
                                on_click=self._handle_run_batch,
                            ),
                            ft.Row(
                                [
                                    ft.IconButton(
                                        ft.Icons.SAVE_OUTLINED,
                                        tooltip="保存批处理方案",
                                        on_click=self._handle_save_universe,
                                    ),
                                    ft.IconButton(
                                        ft.Icons.FOLDER_OPEN_OUTLINED,
                                        tooltip="加载批处理方案",
                                        on_click=self._handle_load_universe,
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        spacing=20,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=12),
            height=80,
            bgcolor=GenshinTheme.HEADER_BG,
            blur=ft.Blur(20, 20),
            border=ft.border.only(bottom=ft.BorderSide(1, GenshinTheme.GLASS_BORDER)),
        )

        self.inspector = MutationInspector(self.state)
        self.content = ft.Stack([self.canvas, self.hud, self.inspector], expand=True)

    def refresh(self):
        self.canvas.refresh()
        self.inspector.refresh()
        # 仅统计叶子节点 (即真正的模拟任务数)
        count = self._count_leaf_nodes(self.state.universe_root)
        try:
            self.hud.content.controls[1].controls[
                0
            ].content.value = f"模拟样本: {count}"
            if self.page:
                self.page.update()
        except:
            pass

    def _count_leaf_nodes(self, node):
        """递归统计叶子节点数量"""
        if not node.children:
            return 1
        return sum(self._count_leaf_nodes(c) for c in node.children)

    async def _handle_run_batch(self, e):
        # 仅执行逻辑，不再弹出摘要对话框
        await self.state.run_batch_simulation()

    def _handle_save_universe(self, e):
        name_f = ft.TextField(label="方案名称", dense=True)

        def confirm(_):
            if name_f.value:
                self.state.save_universe(name_f.value)
                self.page.pop_dialog()

        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("保存批处理方案"),
                content=name_f,
                actions=[ft.ElevatedButton("保存", on_click=confirm)],
            )
        )

    def _handle_load_universe(self, e):
        files = self.state.list_universes()
        lv = ft.ListView(expand=True, spacing=5, height=300)

        def confirm(fname):
            self.state.load_universe(fname)
            self.page.pop_dialog()

        for f in files:
            lv.controls.append(
                ft.ListTile(title=ft.Text(f), on_click=lambda _, n=f: confirm(n))
            )
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("加载方案"), content=ft.Container(lv, width=300)
            )
        )

    def _handle_sync_to_workbench(self, e):
        """实时解析当前选中节点的配置并发送回主进程"""
        config = self.state.get_selected_node_config()
        if config:
            msg = {
                "type": "APPLY_CONFIG",
                "config": config,
                "action_sequence_raw": config.get("action_sequence_raw", []),
            }
            self.state.branch_to_main.put(msg)
            get_ui_logger().log_info(
                f"Sent derived config of node {self.state.selected_node.id} to Workbench."
            )
