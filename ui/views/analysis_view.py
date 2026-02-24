import flet as ft
from ui.theme import GenshinTheme
from ui.states.analysis_state import AnalysisState
from ui.components.analysis.scrubber import GlobalScrubber
from ui.components.analysis.floating_drawer import FloatingDrawer
from ui.components.analysis.tile_container import TileContainer
from ui.components.analysis.dps_tile import DPSChartTile
from ui.components.analysis.summary_tile import SummaryTile
from ui.components.analysis.timeline_tile import TimelineTile
from ui.components.analysis.replay_tile import ReplayTile
from ui.components.analysis.energy_tile import EnergyTile
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
        
        # 1.5 初始化标尺 (预设为 0 帧，待数据加载后更新)
        self.scrubber = GlobalScrubber(max_frames=0, on_change=self._handle_scrub)
        self.scrubber_container = ft.Container(
            content=self.scrubber,
            bottom=0, left=0, right=0, 
            height=45,
            bgcolor="#1E1A2A",
            border=ft.border.only(top=ft.border.BorderSide(1, "rgba(255, 255, 255, 0.08)")),
            padding=ft.padding.only(left=20, right=30, top=0, bottom=0),
            alignment=ft.Alignment(0, 0)
        )
        
        # 2. 聚焦层 (用于最大化显示磁贴)
        self.focus_tile_container = ft.Container(expand=True)
        self.focus_layer = ft.Container(
            content=ft.Stack([
                ft.Container(bgcolor="rgba(0,0,0,0.8)", blur=ft.Blur(20, 20), on_click=lambda _: self._exit_focus_mode()),
                ft.Container(
                    content=self.focus_tile_container,
                    padding=40,
                    alignment=ft.Alignment.CENTER
                ),
                # 移除这里的冗余 ft.IconButton
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

        # 5. 主内容区域 (用于放置工作空间和固定在底部的标尺)
        self.main_content = ft.Stack([
            self.workspace,
            self.scrubber_container
        ], expand=True) # 确保 Stack 纵向拉伸
        
        # 6. 整体布局 Row (工具箱 + 主内容区域)
        self.layout_row = ft.Row([
            self.toolbox,
            self.main_content
        ], spacing=0, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH) # 强制子组件纵向拉伸
        
        self.controls = [
            self.layout_row,
            self.drawer,
            self.focus_layer
        ]
        
        # 订阅分析事件
        if self.app_state:
            self.app_state.events.subscribe("analysis", self._handle_data_ready)
            self.app_state.events.subscribe("audit_detail_ready", self._handle_audit_ready)

    def _handle_data_ready(self):
        """当 AnalysisState 后台抓取完数据库后触发"""
        if self.state.loading: return
        
        from core.logger import get_ui_logger
        get_ui_logger().log_info("AnalysisView: Data ready, assembling tiles...")

        # 如果已经初始化过，且只是数据刷新，则执行磁贴内部更新而不是重绘网格
        if self.active_tiles:
            max_f = self.state.summary.get("duration", 0) * 60
            for tile in self.active_tiles:
                if hasattr(tile, "update_data"):
                    if getattr(tile, "tile_id", "") == "dps":
                        tile.update_data(self.state.dps_points)
                    elif getattr(tile, "tile_id", "") == "summary":
                        tile.update_data(self.state.summary)
                    elif getattr(tile, "tile_id", "") == "timeline":
                        tile.update_data(self.state.action_tracks, self.state.aura_track, max_f)
                    elif getattr(tile, "tile_id", "") == "replay":
                        tile.update_data(self.state.trajectories)
                    elif getattr(tile, "tile_id", "") == "energy":
                        tile.update_data(self.state.energy_data)
            return

        # 1. 更新标尺 (获取总帧数)
        max_f = self.state.summary.get("duration", 0) * 60
        if self.scrubber:
            self.scrubber.max_frames = int(max_f)
            self.scrubber.update_range() # 需要在 GlobalScrubber 中增加此方法或确保其属性响应

        # 2. 初始化磁贴
        self._assemble_tiles()
        
        try: self.update()
        except: pass

    def _handle_audit_ready(self):
        """当单笔伤害审计明细异步加载完成后触发"""
        if self.state.current_audit:
            # 找到抽屉里当前的 AuditPanel 并更新它
            if self.drawer.detail_area.controls:
                panel = self.drawer.detail_area.controls[0]
                if isinstance(panel, AuditPanel):
                    panel.loading = False
                    panel.update_item(self.state.current_audit)

    def _assemble_tiles(self):
        """按需组装首批磁贴"""
        self.grid.controls.clear()
        self.active_tiles.clear()

        # A. 全局概览磁贴 (占 4/12 宽度)
        summary_tile = SummaryTile()
        summary_tile.update_data(self.state.summary)
        summary_container = TileContainer(tile=summary_tile, on_close=self._handle_close_tile)
        summary_container.col = {"sm": 12, "md": 4}
        
        # B. DPS 波动磁贴 (占 8/12 宽度)
        dps_tile = DPSChartTile(on_drill_down=self._handle_drill_down)
        dps_tile.update_data(self.state.dps_points)
        dps_container = TileContainer(tile=dps_tile, on_close=self._handle_close_tile)
        dps_container.col = {"sm": 12, "md": 8}
        
        # 添加到网格
        self.grid.controls.extend([summary_container, dps_container])
        self.active_tiles.extend([summary_tile, dps_tile])

    def _handle_scrub(self, frame_id: int):
        """全局标尺联动回调"""
        for tile in self.active_tiles:
            tile.sync_to_frame(frame_id)

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
        new_tile = None
        col_spec = {"sm": 12, "md": 6}

        if tile_id == "dps":
            new_tile = DPSChartTile(on_drill_down=self._handle_drill_down)
            new_tile.update_data(self.state.dps_points)
            col_spec = {"sm": 12, "md": 8}
        elif tile_id == "summary":
            new_tile = SummaryTile()
            new_tile.update_data(self.state.summary)
            col_spec = {"sm": 12, "md": 4}
        elif tile_id == "timeline":
            new_tile = TimelineTile()
            max_f = self.state.summary.get("duration", 0) * 60
            new_tile.update_data(self.state.action_tracks, self.state.aura_track, max_f)
            col_spec = {"sm": 12, "md": 12} # 时间轴建议全宽
        elif tile_id == "replay":
            new_tile = ReplayTile()
            new_tile.update_data(self.state.trajectories)
            col_spec = {"sm": 12, "md": 6}
        elif tile_id == "energy":
            new_tile = EnergyTile()
            new_tile.update_data(self.state.energy_data)
            col_spec = {"sm": 12, "md": 6}
        
        if new_tile:
            new_tile.tile_id = tile_id
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
        """退出聚焦模式，还原磁贴"""
        if not self.maximized_container: return
        
        # 将 tile 归还
        tile = self.focus_tile_container.content.tile
        self.maximized_container.content_area.content = tile
        self.maximized_container.set_maximized(False)
        
        self.focus_layer.visible = False
        self.maximized_container = None
        self.update()

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
