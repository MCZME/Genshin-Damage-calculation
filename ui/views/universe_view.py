import flet as ft
from ui.theme import GenshinTheme
from core.logger import get_ui_logger
from ui.components.scene.universe_canvas import UniverseCanvas
from ui.components.strategic.mutation_inspector import MutationInspector


class UniverseView:
    """
    分支宇宙编辑器视图 (V4.5 声明式重构版)
    """
    def __init__(self, state):
        self.state = state

    @ft.component
    def build(self):
        # 1. 局部状态 [V4.5 声明式补丁]
        # mode: None | "save" | "load"
        modal_mode, set_modal_mode = ft.use_state(None)
        save_name, set_save_name = ft.use_state("")
        
        count = self._count_leaf_nodes(self.state.universe_root)
        
        # 2. 导航条 (HUD)
        hud = ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.AUTO_AWESOME_MOTION, color=GenshinTheme.PRIMARY, size=20),
                        bgcolor="rgba(209, 162, 255, 0.1)", padding=10, border_radius=12,
                    ),
                    ft.Column([
                        ft.Text("指挥部", size=16, weight=ft.FontWeight.W_900),
                        ft.Text("COMMANDER - 变异树编辑器", size=10, color=GenshinTheme.TEXT_SECONDARY),
                    ], spacing=-3),
                ], spacing=12),
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"模拟样本: {count}", size=11, color=GenshinTheme.PRIMARY, weight=ft.FontWeight.BOLD),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=8),
                        bgcolor="rgba(209, 162, 255, 0.05)",
                        border=ft.border.all(1, GenshinTheme.GLASS_BORDER),
                        border_radius=20,
                    ),
                    ft.ElevatedButton(
                        content=ft.Text("执行批量仿真", weight=ft.FontWeight.BOLD),
                        icon=ft.Icons.PLAY_CIRCLE_FILL_ROUNDED,
                        bgcolor=GenshinTheme.PRIMARY, color=ft.Colors.WHITE,
                        on_click=lambda _: self.state.page.run_task(self.state.run_batch_simulation),
                    ),
                    ft.Row([
                        ft.IconButton(ft.Icons.SAVE_OUTLINED, tooltip="保存批处理方案", on_click=lambda _: set_modal_mode("save")),
                        ft.IconButton(ft.Icons.FOLDER_OPEN_OUTLINED, tooltip="加载批处理方案", on_click=lambda _: set_modal_mode("load")),
                    ], spacing=0),
                ], spacing=20),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding.symmetric(horizontal=32, vertical=12),
            height=80, bgcolor=GenshinTheme.HEADER_BG, blur=20,
            border=ft.border.only(bottom=ft.BorderSide(1, GenshinTheme.GLASS_BORDER)),
        )

        # 3. 遮罩层内容构建
        overlay_dialog = None
        if modal_mode == "save":
            def confirm_save(_):
                if save_name:
                    self.state.save_universe(save_name)
                    set_modal_mode(None)

            overlay_dialog = ft.Container(
                content=ft.Column([
                    ft.Text("保存批处理方案", size=18, weight=ft.FontWeight.BOLD),
                    ft.TextField(label="方案名称", dense=True, on_change=lambda e: set_save_name(e.control.value)),
                    ft.ElevatedButton("执行保存", on_click=confirm_save, bgcolor=GenshinTheme.PRIMARY, color=ft.Colors.WHITE)
                ], spacing=20, tight=True),
                width=400, padding=25, bgcolor=GenshinTheme.SURFACE, border_radius=16, 
                border=ft.Border.all(1, "rgba(255,255,255,0.1)")
            )
        elif modal_mode == "load":
            files = self.state.list_universes()
            lv = ft.ListView(
                controls=[
                    ft.ListTile(
                        title=ft.Text(f), 
                        on_click=lambda _, fname=f: [self.state.load_universe(fname), set_modal_mode(None)]
                    ) for f in files
                ], 
                expand=True, spacing=5, height=300
            )
            overlay_dialog = ft.Container(
                content=ft.Column([
                    ft.Text("加载批处理方案", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(lv, height=350)
                ], spacing=20, tight=True),
                width=450, padding=25, bgcolor=GenshinTheme.SURFACE, border_radius=16,
                border=ft.Border.all(1, "rgba(255,255,255,0.1)")
            )

        return ft.Container(
            content=ft.Stack([
                UniverseCanvas(self.state).build(), # 修正为调用 .build()
                hud,
                MutationInspector(self.state),
                # 声明式遮罩层渲染
                ft.Container(
                    content=ft.Stack([
                        ft.Container(bgcolor="rgba(0,0,0,0.8)", on_click=lambda _: set_modal_mode(None)),
                        ft.Container(content=overlay_dialog, alignment=ft.Alignment.CENTER),
                    ]),
                    visible=modal_mode is not None,
                    expand=True
                )
            ], expand=True),
            expand=True,
            bgcolor=GenshinTheme.BACKGROUND
        )

    def _count_leaf_nodes(self, node):
        """递归统计叶子节点数量"""
        if not node.children:
            return 1
        return sum(self._count_leaf_nodes(c) for c in node.children)

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
