from typing import Any, Dict, List
import flet as ft
import flet_charts as fch
import asyncio
import bisect
import time
from ui.states.analysis_state import AnalysisState
from ui.theme import GenshinTheme
from ui.components.analysis.base_widget import AnalysisTile
from core.persistence.adapter import ReviewDataAdapter
from dataclasses import dataclass, field

@ft.component
def DPSCursor(state: AnalysisState, dps_slot: Any):
    """高性能 DPS 游标子组件 (函数组件版)"""
    # 1. 订阅全局帧状态 (通过读取响应式模型)
    frame_id = state.model.current_frame
    max_frames = max(state.model.total_frames, 1)
    
    # 2. 局部位置计算
    pos_ratio = frame_id / max_frames
    left_pos = (pos_ratio * (800 - 45)) + 18 
    
    # 3. 实时读数计算
    total_val = 0
    if dps_slot and dps_slot.data:
        target_idx = frame_id // 30
        stacked_points = dps_slot.data.get("stacked_points", {})
        for series in stacked_points.values():
            if target_idx < len(series): 
                total_val += series[target_idx]['value']

    return ft.Column(
        left=left_pos,
        controls=[
            ft.Container(
                content=ft.Text(f"{total_val:,.0f}", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                bgcolor=GenshinTheme.GOLD_DARK, 
                padding=ft.Padding.symmetric(horizontal=5, vertical=2), 
                border_radius=4, 
                offset=ft.Offset(-0.5, -1.2)
            ),
            ft.Container(width=2, bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE), expand=True)
        ],
        spacing=0, 
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

class DPSChartTile(AnalysisTile):
    """
    磁贴：DPS 波动曲线 (V4.7 订阅制版)
    """
    def __init__(self, state: AnalysisState, on_drill_down=None):
        super().__init__("DPS 波动曲线", ft.Icons.AUTO_GRAPH, "dps", state)
        self.on_drill_down = on_drill_down
        self.expand = True
        self.palette = [
            GenshinTheme.PRIMARY, ft.Colors.AMBER_400, 
            ft.Colors.BLUE_400, ft.Colors.GREEN_400, ft.Colors.RED_400
        ]

    def render(self):
        # 1. 获取中心化数据槽位
        slot = self.state.data_manager.get_slot("dps")

        if not slot or slot.loading or slot.data is None:
            return ft.Stack([
                ft.Container(content=ft.ProgressRing(width=30, height=30), alignment=ft.Alignment.CENTER, expand=True),
            ], expand=True)

        stacked_data = slot.data.get("stacked_points", {})

        # 构建图表序列
        data_series = []
        num_points = max([len(points) for points in stacked_data.values()] + [0])
        cumulative_y = [0.0] * num_points
        
        legend_controls = []
        for i, (char_name, points) in enumerate(stacked_data.items()):
            color = self.palette[i % len(self.palette)]
            legend_controls.append(ft.Row([
                ft.Container(width=10, height=10, bgcolor=color, border_radius=5),
                ft.Text(char_name, size=11, color=ft.Colors.WHITE_70),
            ], spacing=5))
            
            chart_spots = []
            for point_idx, p in enumerate(points):
                if point_idx < num_points:
                    cumulative_y[point_idx] += p['value']
                    chart_spots.append(fch.LineChartDataPoint(p['frame'], cumulative_y[point_idx]))
            
            data_series.append(fch.LineChartData(points=chart_spots, color=color, stroke_width=2, curved=True, below_line_bgcolor=ft.Colors.with_opacity(0.8, color), point=fch.ChartCirclePoint(radius=0)))
        data_series.reverse()

        return ft.Column([
            ft.Row(controls=legend_controls, spacing=15, wrap=True),
            ft.Stack([
                ft.Container(
                    content=fch.LineChart(data_series=data_series, interactive=True, on_event=self._handle_chart_event, expand=True),
                    padding=ft.Padding(10, 20, 20, 10), expand=True
                ),
                # 渲染函数组件
                DPSCursor(state=self.state, dps_slot=slot)
            ], expand=True)
        ], spacing=10, expand=True)

    def _handle_chart_event(self, e: fch.LineChartEvent):
        slot = self.state.data_manager.get_slot("dps")
        if not slot or not slot.data: return

        raw_events = slot.data.get("raw_events", [])
        frame_indices = slot.data.get("frame_indices", [])

        if e.type == "point_click" and self.on_drill_down and raw_events:
            for spot in e.spots:
                if spot.spot_index != -1:
                    clicked_frame = spot.spot_index * 30
                    idx = bisect.bisect_left(frame_indices, clicked_frame)
                    closest = None
                    if idx == 0: closest = raw_events[0]
                    elif idx >= len(raw_events): closest = raw_events[-1]
                    else:
                        p1, p2 = raw_events[idx-1], raw_events[idx]
                        closest = p1 if abs(p1['frame'] - clicked_frame) < abs(p2['frame'] - clicked_frame) else p2
                    if closest: self.on_drill_down(closest)
                    break

