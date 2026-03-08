import flet as ft
import flet_charts as fch
import bisect
from ui.states.analysis_state import AnalysisState
from ui.components.analysis.base_widget import AnalysisTile

@ft.component
class DPSChartTile(AnalysisTile):
    """
    [V4.0] 专业级 DPS 曲线组件
    支持：多轨堆叠、实时游标、区间缩放
    """
    def __init__(self, state: AnalysisState, on_drill_down=None):
        super().__init__("实时秒伤曲线", ft.Icons.SHOW_CHART_ROUNDED, "dps", state)
        self.on_drill_down = on_drill_down
        self.expand = True
        self.canvas_height = 220
        self.theme_color = "#FFD700"
        self.gradient_top = "#2A2418"

    def render(self):
        """核心渲染：基于 Flet Charts 的高性能绘图"""
        slot = self.state.data_manager.get_slot("dps")
        if not slot or slot.data is None:
            return ft.Container(content=ft.ProgressRing(color=self.theme_color), alignment=ft.Alignment.CENTER, expand=True)

        data = slot.data
        stacked_points = data.get("stacked_points", [])
        
        # 数据转换：适配 LineChart 需要的数据格式
        chart_data = [
            fch.LineChartData(
                data_points=[
                    fch.LineChartDataPoint(p['x'], p['y']) 
                    for p in stacked_points
                ],
                stroke_width=2,
                color=self.theme_color,
                curved=True,
                stroke_cap_round=True,
                below_line_bgcolor=ft.Colors.with_opacity(0.1, self.theme_color),
                below_line_area_stops=[0.0, 1.0],
                below_line_area_colors=[
                    ft.Colors.with_opacity(0.3, self.theme_color),
                    ft.Colors.with_opacity(0.0, self.theme_color)
                ]
            )
        ]

        # 计算游标位置
        total_frames = max(self.state.model.total_frames, 1)
        
        return ft.Container(
            content=fch.LineChart(
                data_series=chart_data,
                border=ft.border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                horizontal_grid_lines=fch.ChartGridLines(interval=10000, width=0.5, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                vertical_grid_lines=fch.ChartGridLines(interval=60, width=0.5, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                left_axis=fch.ChartAxis(
                    labels_size=40,
                    title=ft.Text("DPS", size=10, weight=ft.FontWeight.BOLD),
                    title_size=20,
                ),
                bottom_axis=fch.ChartAxis(
                    labels_size=20,
                    title=ft.Text("Time (s)", size=10, weight=ft.FontWeight.BOLD),
                    title_size=20,
                ),
                tooltip_bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK),
                min_y=0,
                max_y=max([p['y'] for p in stacked_points]) * 1.1 if stacked_points else 100,
                min_x=0,
                max_x=total_frames,
                expand=True,
                animate=False, # 禁用动画以提高实时游标性能
                on_chart_event=self._handle_chart_event
            ),
            padding=ft.Padding(10, 10, 10, 0),
            expand=True
        )

    def _handle_chart_event(self, e: fch.LineChartEvent):
        slot = self.state.data_manager.get_slot("dps")
        if not slot or not slot.data:
            return

        raw_events = slot.data.get("raw_events", [])
        frame_indices = slot.data.get("frame_indices", [])
        
        # 简单的交互逻辑：点击图表同步时间轴
        if e.event_type == "click":
            # 将图表坐标转换回帧数
            # 假设 e.x 是帧数
            if e.x is not None:
                clicked_frame = int(e.x)
                self.state.set_frame(clicked_frame)
                
                # 下钻逻辑
                if self.on_drill_down and raw_events:
                    # 找到最接近该帧的事件
                    idx = bisect.bisect_left(frame_indices, clicked_frame)
                    closest = None
                    if idx == 0:
                        closest = raw_events[0]
                    elif idx >= len(raw_events):
                        closest = raw_events[-1]
                    else:
                        p1, p2 = raw_events[idx-1], raw_events[idx]
                        closest = p1 if abs(p1['frame'] - clicked_frame) < abs(p2['frame'] - clicked_frame) else p2
                    if closest:
                        self.on_drill_down(closest)
                    return
