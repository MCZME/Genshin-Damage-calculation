import flet as ft
import flet_charts as fch
from ui.theme import GenshinTheme
from ui.services.ui_formatter import UIFormatter
from ui.states.analysis_state import AnalysisState
from ui.components.audit_panel import AuditPanel
from ui.components.analysis_metric_card import AnalysisMetricCard

class AnalysisView(ft.Container):
    """
    分析视图重构版 (Analysis View - Data Insights)
    核心：可视化曲线 + 扁平化审计面板。
    """
    def __init__(self, app_state=None):
        super().__init__()
        self.app_state = app_state
        self.state = AnalysisState(app_state=app_state)
        self.expand = True
        self.bgcolor = GenshinTheme.BACKGROUND
        self.padding = 30
        
        self.metric_cards = {} 
        self._has_data = False 
        self._build_ui()
        
        # 订阅分析事件，以便在后台加载完成后刷新 UI
        if self.app_state:
            self.app_state.events.subscribe("analysis", self._handle_data_ready)

    def _handle_data_ready(self):
        """数据就绪回调"""
        if not self.state.loading:
            self._has_data = True
            self._build_ui()
            try: self.update()
            except: pass

    def refresh_data(self):
        """同步加载数据并刷新 UI"""
        from core.logger import get_ui_logger
        sid = getattr(self.app_state, "last_session_id", None)
        get_ui_logger().log_info(f"AnalysisView: refresh_data called. last_session_id={sid}")

        if self.state.loading:
            get_ui_logger().log_info("AnalysisView: Already loading, skipping.")
            return

        self.state.loading = True
        self._build_ui()
        try: self.update()
        except: pass
        
        if self.app_state and sid:
            get_ui_logger().log_info(f"AnalysisView: Triggering state.load_session for SID {sid}")
            self.state.load_session(sid)
            self._has_data = True
            # 注意：load_session 是异步的，后续刷新由 events.notify("simulation") 触发
        else:
            get_ui_logger().log_warning("AnalysisView: last_session_id is None, cannot load data.")
            self.state.loading = False
            self._build_ui()
            try: self.update()
            except: pass

    def did_mount(self):
        """挂载时如果已有数据则直接渲染，否则加载最新会话"""
        if self._has_data and self.state.dps_points:
            self._build_ui()
            try: self.update()
            except: pass
        else:
            self.refresh_data()

    def _on_chart_event(self, e: fch.LineChartEvent):
        """处理图表交互：点击数据点触发审计下钻"""
        # 根据官方文档，e.type 返回事件类型，e.spots 包含交互点列表
        if e.type == "point_click" or e.type == "chart_point_clicked":
            for spot in e.spots:
                # spot_index 是该线上的数据点索引，bar_index 是线的索引
                point_index = spot.spot_index
                if point_index != -1:
                    self.state.select_audit(point_index)
                    self.audit_panel.update_item(self.state.current_audit)
                    try: self.update()
                    except: pass

    def _build_ui(self):
        if self.state.loading:
            self.content = ft.Container(
                content=ft.Column([
                    ft.ProgressRing(color=GenshinTheme.PRIMARY),
                    ft.Text("正在抓取仿真审计数据...", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE24)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                expand=True,
                alignment=ft.Alignment.CENTER
            )
            return

        is_empty = not self.state.dps_points
        
        if is_empty and not self._has_data:
             self.content = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=48, color=ft.Colors.WHITE_12),
                    ft.Text("等待数据初始化...", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE_24),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                expand=True,
                alignment=ft.Alignment.CENTER
            )
             return
        
        # 1. 顶部指标栏 (使用原子组件)
        self.metric_cards = {
            "total_dmg": AnalysisMetricCard("总伤害输出", UIFormatter.format_metric_value(self.state.summary['total_dmg']), ft.Colors.AMBER_400),
            "avg_dps": AnalysisMetricCard("平均 DPS", UIFormatter.format_metric_value(self.state.summary['avg_dps']), GenshinTheme.PRIMARY),
            "duration": AnalysisMetricCard("战斗持续时间", f"{self.state.summary['duration']:.1f}s", ft.Colors.BLUE_200),
            "peak_dps": AnalysisMetricCard("峰值 DPS", UIFormatter.format_metric_value(self.state.summary['peak_dps']), ft.Colors.RED_400),
        }
        self.metrics_row = ft.Row(list(self.metric_cards.values()), spacing=20)

        # 2. 图表区域处理
        if is_empty:
            self.chart_area = self._build_skeleton_chart()
        else:
            self.chart_area = self._build_results_chart()

        # 3. 深度审计面板
        self.audit_panel = AuditPanel(self.state.current_audit)

        # 组装
        self.content = ft.Column([
            ft.Row([
                ft.Text("战后深度数据分析报告", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.REFRESH, on_click=lambda _: self.refresh_data())
            ]),
            self.metrics_row,
            self.chart_area,
            ft.Row([
                ft.Column([
                    ft.Text("动作与状态时间轴 (Action & Aura Lifecycle)", size=12, weight=ft.FontWeight.BOLD, opacity=0.4),
                    self._build_timeline_section(),
                ], expand=2),
                ft.Column([
                    ft.Text("反应触发统计 (Reactions)", size=12, weight=ft.FontWeight.BOLD, opacity=0.4),
                    self._build_reaction_stats_section(),
                ], expand=1),
            ], spacing=25, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Text("每帧伤害审计日志 (点击上方图表点下钻)", size=12, weight=ft.FontWeight.BOLD, opacity=0.4),
            self.audit_panel
        ], spacing=25, scroll=ft.ScrollMode.ADAPTIVE)

    def _build_reaction_stats_section(self):
        """构建反应统计环形图或列表"""
        if not self.state.reaction_stats:
            return ft.Container(
                content=ft.Text("无反应触发数据", size=12, opacity=0.2),
                alignment=ft.Alignment.CENTER, height=150, bgcolor=ft.Colors.BLACK12, border_radius=10
            )

        stats_rows = []
        for r_type, count in self.state.reaction_stats.items():
            stats_rows.append(
                ft.Row([
                    ft.Text(r_type, size=13, weight=ft.FontWeight.W_600, width=100),
                    ft.Container(
                        content=ft.Text(str(count), size=11, weight=ft.FontWeight.BOLD),
                        bgcolor=GenshinTheme.PRIMARY,
                        padding=ft.Padding(8, 2, 8, 2),
                        border_radius=10
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

        return ft.Container(
            content=ft.Column(stats_rows, spacing=10),
            padding=20, bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            border_radius=15
        )

    def _build_skeleton_chart(self):
        """构建骨架屏：带网格与波浪线的占位符"""
        return ft.Container(
            content=ft.Stack([
                ft.Container(
                    content=ft.Column([
                        ft.Divider(height=1, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)) for _ in range(6)
                    ], spacing=40, alignment=ft.MainAxisAlignment.CENTER),
                    expand=True
                ),
                ft.Column([
                    ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=48, color=ft.Colors.WHITE_12),
                    ft.Text("尚未运行仿真", size=16, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE_24),
                    ft.Text("点击下方 [开始仿真] 按钮生成伤害审计报告与 DPS 曲线", size=12, color=ft.Colors.WHITE_12),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            ], alignment=ft.Alignment.CENTER),
            height=320,
            padding=20,
            bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            border_radius=15
        )

    def _build_results_chart(self):
        """真正的图表渲染区：Flet LineChart"""
        data_points = self.state.dps_points
        if not data_points: return self._build_skeleton_chart()
        
        chart_spots = [
            fch.LineChartDataPoint(i, p["value"]) 
            for i, p in enumerate(data_points)
        ]
        
        chart = fch.LineChart(
            data_series=[
                fch.LineChartData(
                    points=chart_spots,
                    color=GenshinTheme.PRIMARY,
                    stroke_width=3,
                    curved=True,
                    below_line_bgcolor=ft.Colors.with_opacity(0.1, GenshinTheme.PRIMARY),
                    below_line_gradient=ft.LinearGradient(
                        begin=ft.Alignment.TOP_CENTER,
                        end=ft.Alignment.BOTTOM_CENTER,
                        colors=[ft.Colors.with_opacity(0.2, GenshinTheme.PRIMARY), ft.Colors.TRANSPARENT]
                    ),
                    point=fch.ChartCirclePoint(radius=4, color=ft.Colors.WHITE),
                )
            ],
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            horizontal_grid_lines=fch.ChartGridLines(interval=max([p["value"] for p in data_points]) / 5, color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            vertical_grid_lines=fch.ChartGridLines(interval=max(len(data_points) / 10, 1), color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            on_event=self._on_chart_event,
            interactive=True,
            expand=True,
        )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.AUTO_GRAPH, size=16, color=GenshinTheme.PRIMARY),
                    ft.Text("DPS 波动曲线 (点击圆点查看审计)", size=12, weight=ft.FontWeight.BOLD),
                ], spacing=10),
                ft.Container(
                    content=chart,
                    padding=10,
                    expand=True
                )
            ], spacing=10),
            height=320,
            padding=20,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, GenshinTheme.PRIMARY)),
            border_radius=15
        )

    def _build_timeline_section(self):
        """构建动作与元素轨道时间轴 (甘特图风格)"""
        if not self.state.lifecycles and not self.state.aura_track:
            return ft.Container(
                content=ft.Text("无生命周期数据", size=12, opacity=0.2),
                alignment=ft.Alignment.CENTER,
                height=100,
                bgcolor=ft.Colors.with_opacity(0.02, ft.Colors.WHITE),
                border_radius=10
            )

        aura_row = ft.Row(spacing=2, scroll=ft.ScrollMode.ADAPTIVE)
        for pulse in self.state.aura_track:
            aura_val = pulse["aura"]
            aura_text = str(aura_val) if aura_val else "None"
            
            # 改进：根据元素名称自动映射主题色
            color = ft.Colors.WHITE24
            for elem, hex_color in GenshinTheme.ELEMENT_COLORS.items():
                if elem in aura_text:
                    color = hex_color
                    break
            
            aura_row.controls.append(
                ft.Container(
                    width=10, height=20, 
                    bgcolor=color,
                    border_radius=2,
                    tooltip=f"Frame {pulse['frame']}: {aura_text}"
                )
            )

        lifecycle_rows = ft.Column(spacing=10)
        max_frame = max([l['end'] or 0 for l in self.state.lifecycles]) if self.state.lifecycles else 600
        if max_frame == 0: max_frame = 600
        scale = 800 / max_frame

        for lc in self.state.lifecycles:
            start_px = lc['start'] * scale
            end_frame = lc['end'] if lc['end'] is not None else max_frame
            duration_px = (end_frame - lc['start']) * scale
            
            color = ft.Colors.BLUE_400 if lc['type'] == 'MODIFIER' else ft.Colors.GREEN_400
            if "Shield" in lc['name']: color = ft.Colors.YELLOW_700

            lifecycle_rows.controls.append(
                ft.Row([
                    ft.Text(lc['name'][:10], size=10, width=80, no_wrap=True),
                    ft.Stack([
                        ft.Container(
                            left=start_px,
                            width=max(duration_px, 2),
                            height=12,
                            bgcolor=ft.Colors.with_opacity(0.3, color),
                            border=ft.Border.all(1, color),
                            border_radius=3,
                        )
                    ], width=820, height=12)
                ], spacing=10)
            )

        return ft.Container(
            content=ft.Column([
                ft.Text("目标附着状态 (Aura Track)", size=10, opacity=0.5),
                ft.Container(content=aura_row, padding=10, bgcolor=ft.Colors.BLACK12, border_radius=8),
                ft.Text("增益与效果覆盖 (Lifecycles)", size=10, opacity=0.5),
                ft.Container(content=lifecycle_rows, padding=10, bgcolor=ft.Colors.BLACK12, border_radius=8),
            ], spacing=15),
            padding=20,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.05, ft.Colors.WHITE)),
            border_radius=15
        )
