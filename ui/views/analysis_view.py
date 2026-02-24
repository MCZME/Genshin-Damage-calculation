import asyncio

import flet as ft
from ui.theme import GenshinTheme
from ui.states.analysis_state import AnalysisState
from ui.components.analysis.scrubber import GlobalScrubber
from ui.components.analysis.floating_drawer import FloatingDrawer
from ui.components.analysis.tile_container import TileContainer
from ui.components.analysis.dps_tile import DPSChartTile
from ui.components.analysis.summary_tile import SummaryTile
# from ui.components.analysis.timeline_tile import TimelineTile
from ui.components.analysis.replay_tile import ReplayTile
from ui.components.analysis.energy_tile import EnergyTile
from ui.components.analysis.history_dialog import HistoryDialog
from ui.components.analysis.toolbox import AnalysisToolbox
from ui.components.audit_panel import AuditPanel

class AnalysisView(ft.Stack):
    """
    分析视图 V3.5 (模块化工作台版)
    采用磁贴网格布局 + 全局时间同步锚点。
    """
    def __init__(self, app_state=None):
        super().__init__()
        self.app_state = app_state
        self.state = AnalysisState(app_state=app_state)
        self.expand = True
        
        # 1. 核心布局组件
        self.toolbox = AnalysisToolbox(on_tile_toggle=self._handle_tile_toggle)
        self.grid = ft.ResponsiveRow(spacing=20, run_spacing=20)
        self.drawer = FloatingDrawer(width=450)
        
        # 1.5 初始化标尺
        self.scrubber = GlobalScrubber(max_frames=0, on_change=self._handle_scrub)
        self.scrubber_container = ft.Container(
            content=self.scrubber,
            height=45,
            bgcolor="#1E1A2A",
            border=ft.border.only(top=ft.border.BorderSide(1, "rgba(255, 255, 255, 0.08)")),
            padding=ft.padding.only(left=20, right=30),
            alignment=ft.Alignment(0, 0)
        )
        
        # 2. 聚焦层 (用于最大化显示磁贴)
        self.focus_tile_container = ft.Container(expand=True)
        self.focus_layer = ft.Container(
            content=ft.Stack([
                ft.Container(bgcolor="rgba(0,0,0,0.7)", on_click=lambda _: self._exit_focus_mode()), # 调低透明度，移除 blur
                ft.Container(
                    content=self.focus_tile_container,
                    padding=40,
                    alignment=ft.Alignment.CENTER
                ),
            ]),
            visible=False,
            expand=True
        )
        
        # 3. 磁贴管理
        self.active_tiles = []
        self.maximized_container = None # 记录当前哪个容器在最大化
        
        # 4. 组装主工作空间
        self.workspace = ft.Container(
            content=ft.Column([
                ft.Container(self.grid, padding=ft.padding.only(bottom=50)), # 配合 45px 的标尺
            ], scroll=ft.ScrollMode.ADAPTIVE, expand=True), # 强制 Column 填满垂直空间
            padding=30,
            expand=True
        )

        # 5. 主内容区域 (由 Stack 改为 Column，大幅提升渲染性能)
        self.main_content = ft.Column([
            self.workspace,
            self.scrubber_container
        ], spacing=0, expand=True) 
        
        # 6. 整体布局 Row (工具箱 + 主内容区域)
        self.layout_row = ft.Row([
            self.toolbox,
            self.main_content
        ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)
        
        self.controls = [
            self.layout_row,
            self.drawer,
            self.focus_layer
        ]
        
        # 订阅分析事件
        if self.app_state:
            self.app_state.events.subscribe("analysis_session_changed", self._handle_session_change)
            self.app_state.events.subscribe("analysis_history_ready", self._show_history_dialog)
            self.app_state.events.subscribe("audit_detail_ready", self._handle_audit_ready)

    def _handle_session_change(self, session_id: int):
        """当会话切换时，通知所有激活磁贴自主加载数据"""
        from core.logger import get_ui_logger
        get_ui_logger().log_info(f"AnalysisView: Session changed to {session_id}, reloading tiles...")

        # 1. 更新标尺范围 (异步获取一次 summary)
        async def _update_scrubber():
            stats = await self.state.adapter.get_summary_stats()
            max_f = stats.get("total_frames", 0)
            if self.scrubber:
                self.scrubber.max_frames = int(max_f)
                self.scrubber.update_range()
        
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_update_scrubber())
        except:
            asyncio.run(_update_scrubber())

        # 2. 如果已经初始化过，通知磁贴刷新
        if self.active_tiles:
            for tile in self.active_tiles:
                if hasattr(tile, "load_data"):
                    tile.load_data(self.state.adapter)
        else:
            # 3. 首次加载，组装磁贴
            self._assemble_tiles()

    def _handle_data_ready(self):
        """[弃用] V4.5 已转向自主加载模式"""
        pass

    def _handle_audit_ready(self):
        """当单笔伤害审计明细异步加载完成后触发"""
        if self.state.current_audit:
            # 找到抽屉里当前的 AuditPanel 并更新它
            if self.drawer.detail_area.controls:
                panel = self.drawer.detail_area.controls[0]
                if isinstance(panel, AuditPanel):
                    panel.loading = False
                    panel.update_item(self.state.current_audit)

    def _show_history_dialog(self):
        """显示历史仿真记录选择对话框 (使用独立组件)"""
        from core.logger import get_ui_logger
        get_ui_logger().log_info(f"AnalysisView: Showing history dialog component...")

        dialog_content = HistoryDialog(
            sessions=self.state.sessions_history,
            on_select=lambda sid: [self.state.load_session(sid), self._exit_focus_mode()],
            on_close=self._exit_focus_mode
        )

        self.focus_tile_container.content = dialog_content
        self.focus_layer.visible = True
        try:
            self.update()
        except:
            pass

    def _assemble_tiles(self):
        """按需组装首批磁贴"""
        self.grid.controls.clear()
        self.active_tiles.clear()

        # A. 全局概览磁贴
        summary_tile = SummaryTile()
        summary_tile.load_data(self.state.adapter)
        summary_container = TileContainer(tile=summary_tile, on_close=self._handle_close_tile)
        summary_container.col = {"sm": 12, "md": 4}
        
        # B. DPS 波动磁贴
        dps_tile = DPSChartTile(on_drill_down=self._handle_drill_down)
        dps_tile.load_data(self.state.adapter)
        dps_container = TileContainer(tile=dps_tile, on_close=self._handle_close_tile)
        dps_container.col = {"sm": 12, "md": 8}
        
        # 添加到网格
        self.grid.controls.extend([summary_container, dps_container])
        self.active_tiles.extend([summary_tile, dps_tile])

    def _handle_scrub(self, frame_id: int):
        """全局标尺联动回调 (局部精准刷新版)"""
        # 仅分发信号，由磁贴执行局部 update()
        for tile in self.active_tiles:
            try:
                tile.sync_to_frame(frame_id)
            except:
                pass

    def _handle_drill_down(self, point_item: dict):
        """点击图表点执行下钻"""
        frame = point_item['frame']
        event_id = point_item['event_id']
        
        # 1. 标尺跳转
        if self.scrubber:
            self.scrubber.set_frame(frame, notify=False)
        
        # 2. 抽屉滑出审计详情 (先显示加载态)
        idx = next((i for i, a in enumerate(self.state.audit_logs) if a.event_id == event_id), -1)
        if idx != -1:
            audit_item = self.state.audit_logs[idx]
            # 立即滑出带加载圈的面板
            panel = AuditPanel(audit_item, loading=True)
            self.drawer.show(content=panel, title=f"伤害审计 - Frame {frame}")
            
            # 触发状态加载明细 (后台异步执行)
            self.state.select_audit(idx)

    def _handle_tile_toggle(self, tile_id: str):
        """处理工具箱磁贴开关请求"""
        # 查找该 ID 是否已在 active_tiles
        existing = next((t for t in self.active_tiles if getattr(t, "tile_id", "") == tile_id), None)
        
        if existing:
            # 如果已存在，则触发对应容器的关闭逻辑
            container = next((c for c in self.grid.controls if getattr(c, "tile", None) == existing), None)
            if container: self._handle_close_tile(container)
        else:
            # 如果不存在，则创建并添加
            self._add_tile_by_id(tile_id)

    def _add_tile_by_id(self, tile_id: str):
        """核心：根据 ID 实例化并部署磁贴"""
        # 特殊处理：历史记录不作为磁贴，而是弹出对话框
        if tile_id == "history":
            self.state.load_history_list()
            return

        new_tile = None
        col_spec = {"sm": 12, "md": 6}

        if tile_id == "dps":
            new_tile = DPSChartTile(on_drill_down=self._handle_drill_down)
            col_spec = {"sm": 12, "md": 8}
        elif tile_id == "summary":
            new_tile = SummaryTile()
            col_spec = {"sm": 12, "md": 4}
        elif tile_id == "replay":
            new_tile = ReplayTile()
            col_spec = {"sm": 12, "md": 6}
        elif tile_id == "energy":
            new_tile = EnergyTile()
            col_spec = {"sm": 12, "md": 6}
        
        if new_tile:
            new_tile.tile_id = tile_id
            if self.state.adapter:
                new_tile.load_data(self.state.adapter) # 核心：自主按需加载
            
            container = TileContainer(
                tile=new_tile, 
                on_close=self._handle_close_tile,
                on_maximize=self._enter_focus_mode
            )
            container.col = col_spec
            
            self.grid.controls.append(container)
            self.active_tiles.append(new_tile)
            self._update_toolbox_highlight()
            self.update()

    def _update_toolbox_highlight(self):
        """同步工具箱图标状态"""
        active_ids = [t.tile_id for t in self.active_tiles if hasattr(t, "tile_id")]
        self.toolbox.update_active_states(active_ids)

    def _enter_focus_mode(self, container):
        """进入沉浸式聚焦模式"""
        self.maximized_container = container
        # 暂时将 tile 从原容器移出，放入聚焦层
        tile = container.tile
        container.content_area.content = ft.Container() # 占位
        
        self.focus_tile_container.content = TileContainer(
            tile=tile,
            on_maximize=lambda _: self._exit_focus_mode(), # 最大化按钮变为退出
            on_close=lambda _: self._exit_focus_mode(),
            is_maximized=True
        )
        
        self.focus_layer.visible = True
        self.update()

    def _exit_focus_mode(self):
        """退出聚焦模式，还原磁贴或关闭浮层"""
        if self.maximized_container:
            # 如果是从磁贴最大化退出，执行归还逻辑
            tile = self.focus_tile_container.content.tile
            self.maximized_container.content_area.content = tile
            self.maximized_container.set_maximized(False)
            self.maximized_container = None
        
        # 无论是否有磁贴最大化，都隐藏聚焦层并清空内容
        self.focus_layer.visible = False
        self.focus_tile_container.content = ft.Container()
        try:
            self.update()
        except:
            pass

    def _handle_close_tile(self, container):
        self.grid.controls.remove(container)
        if container.tile in self.active_tiles:
            self.active_tiles.remove(container.tile)
        self._update_toolbox_highlight()
        self.update()

    def refresh_data(self):
        """外部主动触发刷新"""
        sid = getattr(self.app_state, "last_session_id", None)
        if sid:
            self.state.load_session(sid)
